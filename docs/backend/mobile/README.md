# docs/backend/mobile — Sprint 11, Lote 9 (Mobile / App Motorista)

Documentação de implementação do bounded context `mobile` — Sessão Mobile, Dispositivo Mobile, Fila
de Sincronização, Registro de Sincronização, Assinatura Digital. Escopo confirmado pelo usuário:
exatamente as 5 entidades já congeladas em `dictionary/009-app_motorista.md`/
`relational/009-app_motorista.md`, e os endpoints já congelados em `054-driver-authentication.md` a
`061-driver-devices.md` — sem Checklist físico (D305, ainda documentação-only).

| Documento | Cobre |
|---|---|
| [`AUTHENTICATION_AND_DEVICE_IMPLEMENTATION.md`](./AUTHENTICATION_AND_DEVICE_IMPLEMENTATION.md) | `SessaoMobile` (D407/D408/D409), `MobileDevice` |
| [`SYNC_IMPLEMENTATION.md`](./SYNC_IMPLEMENTATION.md) | `SyncQueueItem`/`SyncRecord` (D410), reuso de comandos de Viagem/Entrega/Ocorrência/Canhoto (D411) |

Tudo em `modules/mobile/` — RBAC `mobile.*` (§7.27) para a infraestrutura própria (Sessão/
Dispositivo/Sync); toda ação de domínio (aceitar/iniciar/finalizar viagem, ocorrência, entrega,
canhoto) continua usando os códigos do módulo dono (`freight.*`), nunca uma segunda autorização
(D303).

## Princípio central: o app é cliente do domínio, nunca um domínio paralelo

`mobile` não redefine nenhuma regra de negócio de Viagem/Entrega/Ocorrência/Canhoto — todas
pertencem a `freight`. O que `mobile` de fato possui é a experiência de campo: sessão, dispositivo,
fila offline e assinatura. Concretamente: os cinco comandos de Viagem
(`accept`/`start`/`interromper`/`retomar`/`finish`), `RegisterOccurrence`, `CreateDelivery` e
`RegisterProofOfDelivery` são chamados a partir de `modules/mobile` **exatamente pelas mesmas
classes** `Handler` já usadas por `modules/freight/interfaces/api/*.py` — nunca reimplementados.

## `TrackingIngestion`-style não se aplica aqui — o inverso do Lote 8

Diferente de Rastreamento (onde não havia nenhum jeito de dado entrar, D402), aqui o problema é o
oposto: os comandos de domínio **já têm** endpoint HTTP direto (`014`-`019`). O que falta é o
caminho **assíncrono/offline** — a Fila de Sincronização — que precisa, no fim, invocar exatamente
os mesmos `Handler`s. Resolvido com uma tabela de despacho (`SYNC_COMMAND_HANDLERS`, D410)
compartilhada pelos dois caminhos (`/mobile/trips/{id}/commands/X` direto e `/mobile/sync` via
fila), nunca duas implementações.

## Critério de Definição de Pronto (D352) + 8 auditorias explícitas do usuário

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation + auditoria
comprovados por teste — mais as oito auditorias pedidas explicitamente antes de fechar o lote:

1. **Offline/idempotência** — reenviar o mesmo `identificador_local_unico` produz um único efeito.
2. **Ordem da fila** — processamento por `sequencia_local`, nunca pela ordem de chegada HTTP.
3. **Conflito** — comando offline válido na origem, inválido na sincronização (ex: `finish` de uma
   Viagem já `CANCELADA`) — backend registra `CONFLITO`, preserva o payload original.
4. **Sessão × Dispositivo** — revogar a Sessão nunca desativa o Dispositivo; bloquear/desativar o
   Dispositivo impede novas sessões.
5. **Tenant/identidade** — `motorista_id`/`tenant_id` nunca vêm do corpo da requisição, sempre da
   sessão autenticada.
6. **RBAC** — a API mobile reutiliza os mesmos códigos/comandos de domínio da Viagem.
7. **Push** — atualização de `push_token` permanece metadata de dispositivo, nunca altera Viagem.
8. **Storage** — fotos/canhotos/assinaturas sempre `arquivo_id`, nunca binário/base64.

Mais a auditoria adicional proposta pelo usuário: o mesmo comando via endpoint Web direto e via
sincronização Mobile produz a mesma transição e o mesmo efeito de domínio (validação concreta de
D303).

## Achados deste lote (Sprint 11, Lote 9)

Migration aplicada com sucesso na primeira tentativa (`alembic upgrade head`), sem nenhum ajuste
manual de constraint — ao contrário dos Lotes 7/8, cujas tabelas particionadas/PostGIS exigiam
correção manual pós-autogenerate. As 5 tabelas deste lote (`sessoes_mobile`, `dispositivos_mobile`,
`filas_sincronizacao`, `registros_sincronizacao`, `assinaturas_digitais`) não são particionadas,
então o autogenerate só carregou os falsos-positivos D360-family já conhecidos (drop/recreate de
tabelas `_default`/`spatial_ref_sys` de lotes anteriores), removidos do arquivo antes de aplicar.

Suíte final: 156 testes passando (144 do Lote 8 + 12 novos deste lote), zero regressão. `ruff`,
`mypy --strict` (1236 arquivos) e os 10 contratos de `import-linter` (incluindo o carve-out
`modules.mobile` → `modules.freight` documentado em `pyproject.toml`) passam limpos no repositório
inteiro, não só em `modules.mobile`.

Achados reais, todos vindos de execução real (Postgres/HTTP), não de leitura de código:

1. **Gap real encontrado e corrigido antes de qualquer teste** — `MobileLoginHandler` inicialmente
   não checava o `status` de um Dispositivo já existente antes de permitir login, o que violava
   silenciosamente a Auditoria #4 explícita do usuário ("bloquear/desativar o dispositivo deve
   impedir novas sessões"). Corrigido adicionando a checagem `DeviceStatus.ATIVO` em
   `login.py` antes de qualquer nova Sessão Mobile ser criada — auto-detectado durante o desenho do
   cenário de teste, antes de rodar qualquer coisa contra o banco.
2. **D396 (Lote 7) se aplica diretamente ao Motorista** — `/mobile/trips/{id}/commands/start` chama
   o mesmo `DispatchTripHandler` do endpoint Web, que dispara criação automática de CT-e
   (`FISCAL_CONFIG_NOT_FOUND` se o tenant não tiver `FiscalConfiguration`). Só foi descoberto
   rodando a Auditoria #2 (ordem da fila) contra o Postgres real — nenhuma leitura de código isolada
   dos routers `mobile` revelaria essa dependência transitiva de `documents`, porque ela mora dentro
   de `freight.application.commands.dispatch_trip`, dois módulos "de distância" do endpoint mobile
   chamado. Prova concreta de que reusar o `Handler` exato (D303/D410) também importa os efeitos
   colaterais reais dele, não só a transição de estado — exatamente o comportamento correto.
3. **Idempotência (Auditoria #1) tem uma superfície mais estrita do que "reprocessar e comparar"** —
   como `list_pending_ordered` só devolve itens `PENDENTE`/`FALHOU`, reenviar um `local_id` já
   `PROCESSADA` não aparece de novo no array `results` da segunda chamada: a resposta vem com
   `results: []`. A prova de idempotência correta não é "o segundo resultado é igual ao primeiro", é
   "o segundo resultado não reprocessa nada" — mais forte, e só ficou claro rodando contra o banco
   real (a primeira versão do teste assumia incorretamente um resultado espelhado).
4. **Unicidade de alocação de Veículo é por Veículo, não por Viagem** — a Auditoria adicional (mesmo
   comando via Web e via Mobile) inicialmente tentou alocar o mesmo par Motorista+Veículo em duas
   Viagens simultâneas; `FREIGHT_VEHICLE_UNAVAILABLE` (regra já existente desde o Lote 5,
   `exists_vigente_for_vehicle_excluding_trip`) rejeitou a segunda alocação — confirma que a regra
   "um Veículo Tracionador só pode estar VIGENTE em uma Viagem por vez" continua sendo aplicada
   corretamente mesmo quando as duas Viagens são criadas para provar um comportamento não
   relacionado a frota.

## Decisões

D407–D411 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: BI, depois IA.
