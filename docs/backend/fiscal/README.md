# docs/backend/fiscal — Sprint 11, Lote 7 (Fiscal)

Documentação de implementação do bounded context `documents` — CT-e, MDF-e, CIOT, Carta de
Correção, NF-e Referenciada, Evento Fiscal, Configuração Fiscal do Tenant. Escopo confirmado pelo
usuário: exatamente os agregados já congelados em `039-cte.md` a `045-configuracao-fiscal.md`,
nenhuma mudança estrutural na OpenAPI/modelo relacional.

| Documento | Cobre |
|---|---|
| [`CTE_IMPLEMENTATION.md`](./CTE_IMPLEMENTATION.md) | `CTe` (máquina de 8 estados) |
| [`MDFE_IMPLEMENTATION.md`](./MDFE_IMPLEMENTATION.md) | `MDFe` (máquina de 4 estados, `mdfes_ctes` N:N) |
| [`CIOT_IMPLEMENTATION.md`](./CIOT_IMPLEMENTATION.md) | `CIOT` |
| [`CORRECTION_AND_REFERENCE_IMPLEMENTATION.md`](./CORRECTION_AND_REFERENCE_IMPLEMENTATION.md) | `CorrectionLetter` (Carta de Correção), `ReferencedNFe` (NF-e Referenciada) — sub-recursos de CT-e |
| [`FISCAL_EVENTS_IMPLEMENTATION.md`](./FISCAL_EVENTS_IMPLEMENTATION.md) | `FiscalEvent` (log técnico bruto, D105/D277) |
| [`CONFIGURATION_IMPLEMENTATION.md`](./CONFIGURATION_IMPLEMENTATION.md) | `FiscalConfiguration` (numeração/certificado/série/ambiente) |

Tudo em `modules/documents/` — RBAC `documents.*` (§7.17), já totalmente presente antes deste lote
(primeiro lote da sprint sem nenhuma lacuna de RBAC a corrigir — `documents.fiscal_config.*` já
tinha sido adicionado em D283, Sprint 10 Lote 8).

## Cross-module Application→Application (D390/D396/D398)

Três pares deste lote, mesmo formato "consumidor futuro de evento, síncrono porque nenhum EventBus
real está religado" (D247/D375):

1. **`freight`→`documents` (D396, novo, primeira vez nesta direção)**: `DispatchTripHandler`
   (`freight`) chama `CreateCteHandler` (`documents`) logo após a Viagem transicionar
   `LIBERADA→EM_DESLOCAMENTO` — `Sem POST /ctes` (`039-cte.md`), o único jeito de um CT-e nascer é
   este gatilho.
2. **`documents`→`freight` (D398)**: CT-e `AUTORIZADO`/`CANCELADO` e MDF-e `AUTORIZADO`/`ENCERRADO`
   chamam `TripInternalTransitions().record_fiscal_transition(...)` (mesma classe já usada por
   `financial`, D390) para atualizar a projeção resumida `Trip.status_fiscal`.
3. **`documents`→`freight`, leitura (D356-style)**: `commands/close` do MDF-e valida a precondição
   "última Entrega da Viagem concluída" lendo `DeliveryRepository.count_pending_for_trip()`
   diretamente — mesmo padrão de leitura cross-module já usado pela precondição de Fatura (D388,
   Lote 6).

## `FiscalInternalTransitions` — simulador das duas transições genuinamente externas (D397)

CT-e `TRANSMITIDO→AUTORIZADO`/`DENEGADO` e MDF-e `PENDENTE→AUTORIZADO` são respostas assíncronas da
SEFAZ — nenhum endpoint HTTP as dispara (`039`/`040`, "Externa"). `FiscalInternalTransitions` (mesmo
espírito de `TripInternalTransitions`, D376) simula essa resposta: grava um `EventoFiscal`
(`RESPOSTA`) + a linha de `*_status_history`, idempotente por `protocolo_sefaz`. Testes chamam este
método diretamente, nunca via HTTP.

**CIOT não precisa disso** — `commands/register` (`041-ciot.md`) é uma chamada síncrona real que já
volta com `ciot_code`/`protocolo_antt` na mesma resposta HTTP, sem separação requisição/resposta
como CT-e/MDF-e.

## Numeração atômica (D399)

`configuracoes_fiscais_tenant.proximo_numero_cte`/`.proximo_numero_mdfe` incrementados via
`SELECT ... FOR UPDATE` na linha da configuração do tenant, dentro da mesma transação da criação do
CT-e/MDF-e — `numero` gravado no documento é sempre a cópia do valor já incrementado (D110), nunca
recalculado depois. Prova por teste: criar dois documentos em sequência confirma números
consecutivos nunca reutilizados.

## `duracao_ms` é `GENERATED` (reaplicação de D382)

`eventos_fiscais.duracao_ms` depende só de duas colunas da própria linha
(`data_hora_fim − data_hora_inicio`) — mapeado com `sqlalchemy.Computed(...)`, mesmo fix que D382
(Lote 5) precisou descobrir por um teste falhando; aqui aplicado proativamente desde o primeiro
rascunho do model.

## `eventos_fiscais` é particionada (reaplicação de D346/D364)

`PARTITION BY RANGE (data_hora_inicio)` criada via SQL bruto na migration, com uma partição
`DEFAULT` — mesmo padrão de `logs_auditoria`/`leituras_hodometro`/`viagem_status_history`.

## `audit` parcial ou omitido (D400) — mudança de precedente vs. D391

`CTe`/`MDFe`/`CIOT`/`FiscalConfiguration` exigem `audit: AuditMetadata` no schema, mas a DDL
congelada não tem as colunas completas (`ctes` só tem `criado_em`/`atualizado_em`; `mdfes`/`ciots`/
`configuracoes_fiscais_tenant` não têm nenhuma). Diferente de D391 (Lote 6, que retrofitou colunas),
aqui `CTeResponse.audit` é parcialmente populado com o que existe de verdade (`created_by`/
`updated_by` sempre `None`) e `MDFeResponse`/`CIOTResponse`/`FiscalConfigurationResponse` **omitem**
`audit` — porque este lote está sob a instrução explícita do usuário de evitar alterações
estruturais no modelo relacional. Mesmo tratamento de `Delivery.audit`, D381.

## XML/certificado/payload nunca inline (D107, reforçado por teste)

`xml_arquivo_id` (CT-e/MDF-e/Carta de Correção/NF-e Referenciada), `certificado_arquivo_id`
(Configuração Fiscal) e `payload_arquivo_id` (Evento Fiscal) são sempre `UUID` sem FK física (mesmo
padrão de `anexos`/`comentarios`) — nenhuma entidade de domínio tem um campo de texto/blob para
conteúdo de arquivo. Auditoria #2 do usuário prova isso por introspecção de schema/tabela.

## Auditorias pedidas explicitamente pelo usuário antes de fechar o lote

1. **Idempotência** — retransmitir o mesmo protocolo SEFAZ/reenviar o mesmo evento ANTT nunca cria
   registro duplicado nem uma segunda transição. Ver `FiscalInternalTransitions` acima.
2. **XML nunca inline** — só `xml_arquivo_id`/`payload_arquivo_id` são persistidos, nunca o
   conteúdo.
3. **Máquinas de estado** — cada transição grava exatamente uma linha em `*_status_history`.
4. **Numeração congelada** — o número vem da Configuração Fiscal, é copiado no documento na
   emissão, e permanece congelado mesmo que a Configuração mude depois.
5. **Reprocessamento de evento** — reenviar o mesmo callback SEFAZ/ANTT não duplica linhas em
   `eventos_fiscais`.

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation +
auditoria comprovados por teste — mais as cinco auditorias explícitas acima.

## Achados deste lote (Sprint 11, Lote 7)

`alembic upgrade head` criou as 11 tabelas novas (`configuracoes_fiscais_tenant`/`ctes`/`ctes_
status_history`/`mdfes`/`mdfes_ctes`/`mdfes_status_history`/`ciots`/`ciots_status_history`/
`cartas_correcao`/`nfe_referenciadas`/`eventos_fiscais`) contra o Postgres portátil. Dois ajustes
manuais reais na migration, além do falso-positivo recorrente de partição já conhecido: (1)
`eventos_fiscais` precisou nascer via SQL bruto com `PARTITION BY RANGE (data_hora_inicio)` + `GENERATED`
(reaplicação proativa de D346/D364/D382 — desta vez sem precisar de um teste falhando para
descobrir, já que a lição de Lote 5 estava fresca); (2) `uq_eventos_fiscais_documento_protocolo`
precisou incluir `data_hora_inicio` — Postgres exige que toda constraint `UNIQUE` de tabela
particionada inclua a coluna de partição (mesma família D201/D202, Sprint 09), achado só ao rodar
`alembic upgrade head` de verdade contra o banco real, não visível em nenhum documento em prosa.
`ruff`/`mypy --strict`/`lint-imports` passaram limpos na primeira execução. A suíte de integração
encontrou dois bugs de implementação reais na primeira rodada (D401) — `Cte.validate()` tinha uma
checagem `valor_servico > 0` inventada que bloqueava o caso mais comum, e `FiscalInternalTransitions`
deixava `xml_arquivo_id` `None` mesmo em `AUTORIZADO` — ambos corrigidos antes de fechar o lote. A
suíte fecha em **127 passed, 0 failed** (111 acumulados + 16 novos de Fiscal; Redis/RabbitMQ/MinIO
continuam fora do ambiente de build). As cinco auditorias explícitas do usuário foram todas
verificadas por teste real contra HTTP + Postgres:

1. **Idempotência** — `TestIdempotencyAndEventReprocessingAudit`: reenviar a mesma resposta SEFAZ
   (mesmo `protocolo_sefaz`) três vezes seguidas nunca gera uma segunda linha `AUTORIZADO` em
   `ctes_status_history` nem um segundo `EventoFiscal`.
2. **XML nunca inline** — `TestXmlNeverInlineAudit`: `GET /ctes/{id}/xml` e `FiscalEvent.payload_
   file_id` sempre devolvem um UUID de referência, nunca conteúdo; XML indisponível antes de
   `AUTORIZADO` retorna `404` explícito.
3. **Máquinas de estado** — `TestCteFlow`/`TestMdfeFlow`/`TestCiotFlow`: contagem exata de linhas
   em `*_status_history` a cada transição real (5 para o ciclo completo de CT-e, 2 para MDF-e, 1
   para CIOT).
4. **Numeração congelada** — `TestNumberingFrozenAudit`: segundo CT-e emitido continua a numeração
   de onde o primeiro parou e adota a nova série só a partir de si mesmo; o primeiro CT-e nunca
   muda depois que a Configuração Fiscal é alterada.
5. **Reprocessamento de evento** — coberto na mesma classe da auditoria #1, com um segundo teste
   dedicado ao CIOT/ANTT provando que `eventos_fiscais` nunca duplica pelo mesmo protocolo.

## Decisões

D396–D401 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: Sprint 11 Lote 8 — Rastreamento.
