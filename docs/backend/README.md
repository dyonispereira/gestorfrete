# docs/backend — Sprint 11 (Implementação do Backend)

Índice da documentação técnica do Backend real (`apps/api/`), contraparte executável de
[`docs/architecture/`](../architecture/) (o "porquê", Fase 0). Onde os dois divergirem,
`docs/backend/` vence — é descrição de código que existe e passa em teste, não de intenção.

## Backend Freeze (concluído e aprovado — D427/D428/D429)

Auditoria mecânica de sete frentes fechando a Sprint 11 antes do Frontend: OpenAPI↔FastAPI (326/333
rotas reais casadas com o contrato, **zero rotas de negócio sem contrato** depois de D429, dois
bugs de contrato corrigidos na fonte), RBAC↔Endpoints (zero código de permissão inventado nos 404
códigos oficiais, 100% dos endpoints de negócio protegidos), banco vazio→Alembic HEAD (schema
byte-a-byte idêntico ao ambiente de desenvolvimento — 109 tabelas, 1111 constraints, 237 índices, 9
partições), infraestrutura real (Redis e RabbitMQ reais pela primeira vez em toda a Sprint 11, via
binários portáteis — mesmo espírito de PostGIS/MinIO), suíte completa (191 passed, zero
deselecionados por infra ausente — um bug real de cleanup de conexão RabbitMQ encontrado e
corrigido) e qualidade arquitetural (ruff/mypy --strict/import-linter/migrations/OpenAPI lint todos
limpos). Relatório completo com todos os números mecanicamente extraídos em
[`BACKEND_FREEZE.md`](./BACKEND_FREEZE.md).

Usuário aprovou o Freeze e decidiu o único achado pendente: `POST /mobile/trips/{id}/deliveries`
(mais o comando de sincronização equivalente `REGISTER_DELIVERY`, mesmo Handler) removido do
Backend — **D429** ("Rota não contratada é removida no Freeze": reaproveitamento de Handler nunca
autoriza uma nova superfície HTTP fora do contrato congelado). Reauditado mecanicamente após a
remoção: zero rotas de negócio remanescentes sem contrato. Os 55 gaps restantes (contrato existe,
Backend não implementa) foram classificados explicitamente: 53 **DELIBERADAMENTE_ADIADO** (têm
decisão própria — D417 Manutenção/OS, D332 Filiais, D272 Assinatura/Cobrança, D385 Conciliação
Bancária/Posição de Caixa) e 2 **FALTANTE** — `forgot-password`/`reset-password`, sem decisão de
exclusão, destacadas por impactarem diretamente a futura tela de Login/Recuperação do Frontend
(Sprint 12, Lote 2). D427 (Backend Freeze), D428 (ambiente limpo como critério de release) e D429
(rota não contratada removida) registradas.

## Lote 12 — IA (concluído)

Segundo lote da retomada explícita do usuário ("Retomar BI → IA → fechar Backend transversalmente →
Frontend"), imediatamente depois do Lote 11 (BI). Um único bounded context — `ai` — 8 entidades
(Modelo de IA, Inferência de IA, Sugestão de IA, Predição de IA, Classificação de IA, Anomalia
Detectada, Leitura por Visão Computacional, Feedback de IA), 8 tabelas físicas (`inferencias_ia`
particionada mensalmente por `data_hora_inicio`, D201). Princípio central D161/D164 ("IA sugere,
nunca decide; nunca substitui o dado bruto") ganhou mecanização própria: D426, terceiro contrato
`import-linter` módulo-inteiro-contra-módulo-inteiro do projeto (mesmo formato do D405/D421),
provado por injeção deliberada de violação (mesmo precedente dos Lotes 1/11) — o gate barrou a
violação imediatamente, revertida em seguida. D170 (fornecedor agnóstico) ganhou sua própria
mecanização: `AIModelGateway` (port `ABC`) + `FakeAIModelGateway` (única implementação,
determinística, sem chamada de rede) — nenhuma linha de `domain`/`application` importa SDK de
provedor real, verificado por teste AST-based. `AIInferenceEngine` (D424, mesma família de
`TripInternalTransitions`/`AnalyticsCalculationEngine`) é o único lugar que executa o gateway e cria,
na mesma transação, a Inferência técnica + exatamente uma saída de negócio. Documentação de
implementação em [`ai/README.md`](./ai/README.md) (e o documento que ele indexa).

Aplicou o D352 às 8 entidades mais as 10 auditorias explicitamente pedidas pelo usuário — 14 testes
novos (`test_ia_flow.py`), todos passando na primeira execução completa contra Postgres real. Um
achado físico real (não apenas de contrato): a DDL congelada declara `inferencia_ia_id UUID
REFERENCES inferencias_ia(id)` nas 5 tabelas de saída de IA, mas isso é fisicamente impossível — o
Postgres exige que toda constraint `UNIQUE` de uma tabela particionada inclua a coluna de partição, e
`inferencias_ia` é particionada (D201); confirmado tentando a migration contra o Postgres real e
recebendo `FeatureNotSupportedError` antes da correção. Resolvido removendo a FK física das 5
tabelas (mesma coluna, sem `REFERENCES`) — integridade garantida pela aplicação, nunca pelo banco
(D202 já previa esse tipo de resolução). A auditoria de "fornecedor agnóstico" (D170) quase deu falso
positivo num grep textual ingênuo, que confundia os próprios docstrings explicativos do código
(citando "nunca importa OpenAI/Anthropic/...") com uso real — corrigido para AST real
(`import`/`from`). `ck_leituras_visao_computacional_confirmacao_humana` provado nos dois níveis:
Application recusa antes do banco, e um teste separado contorna a Application via SQL bruto para
confirmar que a constraint física também rejeita. `ruff`/`mypy --strict` (1538 arquivos)/
`lint-imports` (12/12 contratos, `ai` adicionado aos dois contratos compartilhados + o novo D426)
passaram limpos no repositório inteiro. A suíte fecha em **141 passed, 2 deselected** (Redis/
RabbitMQ, pendência de infraestrutura pré-existente desde o Lote 1, não afetada por este lote) —
detalhe completo em [`ai/README.md`](./ai/README.md#achados-deste-lote-sprint-11-lote-12). D423–D426
registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 11 — BI (concluído)

Primeiro lote depois que o usuário decidiu explicitamente retomar o escopo que havia sido adiado
(`062`-`070`), em vez de seguir para o Frontend: "Retomar BI → IA → fechar Backend transversalmente →
Frontend". Dois bounded contexts — `analytics` (Métrica, Indicador Consolidado, Snapshot Analítico,
Cubo Analítico) e `reporting` (Dashboard, Filtro Favorito, Relatório Salvo, Exportação, Agendamento
de Atualização) — 9 entidades, 12 tabelas físicas (incluindo 3 tabelas de junção N:N). Princípio
central D090/D149 ("BI lê os módulos operacionais, nenhum módulo operacional depende de BI") ganhou
mecanização própria: D421, segundo contrato `import-linter` módulo-inteiro-contra-módulo-inteiro do
projeto (mesmo formato do D405/Lote 8), provado por injeção deliberada de violação (mesmo precedente
do Lote 1/`DEPENDENCY_RULES.md`) — o gate barrou a violação imediatamente, revertida em seguida.
`AnalyticsCalculationEngine` (D420, mesma família de `TripInternalTransitions`) é a prova mecânica
real: lê `viagens.receita_realizada` via `SqlAlchemyTripRepository`, cross-module de verdade, sem
mock. Documentação de implementação em [`bi/README.md`](./bi/README.md) (e os 2 documentos que ele
indexa).

Aplicou o D352 às 9 entidades mais as 8 auditorias explicitamente pedidas pelo usuário — 7 testes
novos (`test_bi_flow.py`), todos passando na primeira execução completa contra Postgres real. Um
achado de projeto (D419: versionamento de Métrica sem coluna de encadeamento — nova versão é sempre
uma linha física nova, "atual" resolvido por `ORDER BY versao DESC`) e um achado de contrato (D422:
`066`-`068`/`bi-schemas.md` prometem soft delete + `audit` em Dashboard, mas a DDL congelada não tem
nenhuma coluna de auditoria nas 5 tabelas de `reporting` — resolvido reaproveitando o enum `status`
existente como mecanismo físico de soft delete, `DashboardResponse` omite `audit`, mesmo precedente
de `IntegrationConfigResponse`/`WebhookResponse` do Lote 10). Dois achados de entidade corrigidos
antes de qualquer migration (nunca chegaram a existir fisicamente no banco): `AnalyticalSnapshot`
quase ganhou uma coluna `metricas_participantes` que a DDL não tem (D160 é sempre derivado via JOIN);
`Dashboard` quase ganhou um `audit: AuditMetadata` real antes do achado D422 acima. Um bug pego pelo
primeiro teste de integração: os 3 novos `DELETE` (`dashboard`/`saved_filter`/`saved_report`)
esqueceram `response_model=None` no decorator — toda rota `DELETE 204` do projeto (24 anteriores)
sempre passa esse parâmetro. `ruff`/`mypy --strict` (1438 arquivos)/`lint-imports` (11 contratos,
`analytics`/`reporting` adicionados aos contratos compartilhados + D421 novo) passaram limpos no
repositório inteiro. A suíte fecha em **127 passed, 2 deselected** (Redis/RabbitMQ, pendência de
infraestrutura pré-existente desde o Lote 1, não afetada por este lote) — detalhe completo em
[`bi/README.md`](./bi/README.md#achados-deste-lote-sprint-11-lote-11). D418–D422 registradas em
[`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 10 — Recursos Transversais (concluído)

Último bounded context com contrato OpenAPI congelado e ainda sem Backend, depois que o usuário
adiou BI (`062`-`070`) e IA (`071`-`077`) para um sprint futuro. Quatro subsistemas pequenos em vez
de um domínio central: `storage` (`File`, primeiro I/O binário real do backend, contra MinIO
instalado como binário portátil sem Docker — D412), `Attachment`/`Comment` sobre Viagem (camada HTTP
nova sobre entidades já existentes desde o Lote 5, D371/D316), Busca Global e extensão da Timeline
Universal (compositores finos sem bounded context próprio, D317/D416), `notification_center`
(`Notificação`/`Preferência de Canal`, D323, conjunto mínimo de 2 eventos por D414) e `integration`
(`Configuração de Integração`/`Webhook`/`Execução de Job`, entrega/execução real simuladas via
`*InternalTransitions` por D413, já que os próprios contratos `088`/`089` mantêm isso fora do
escopo HTTP). `084`/`085` (Relatórios/Exportações) não geram código — reconciliados com o Lote 11/
BI, também adiado (D326). Documentação de implementação em
[`transversais/README.md`](./transversais/README.md) (e os 4 documentos que ele indexa).

Aplicou o D352 aos 4 subsistemas reais mais as auditorias documentadas em cada sub-documento — 11
testes novos, todos passando na primeira execução real, incluindo upload/download binário genuíno
contra MinIO (URL assinada real, hash SHA-256 calculado e conferido, round-trip byte-a-byte).
`alembic upgrade head` criou 6 tabelas na primeira tentativa. Dois achados arquiteturais registrados
(D415: `File` precisa nascer `ATIVO` já no `POST /uploads`, já que `arquivos_status_enum` não tem
estado intermediário; D417: Busca Global exclui `ordem_servico` porque `Ordem de Serviço` nunca foi
implementada no Backend). Encontrou e corrigiu uma regressão real em `test_mobile_flow.py` (Lote 9)
— `Notificação` passou a nascer como efeito colateral de `DispatchTripHandler`/
`CreateOccurrenceHandler`, já existentes, e o `_cleanup_tenant` daquele arquivo não conhecia a
tabela nova — mais um bug latente pré-existente que essa mesma regressão expôs (uma asserção de
teste do Lote 9 consultava `filas_sincronizacao` sem filtrar por tenant). `ruff`/`mypy --strict`
(1326 arquivos)/`lint-imports` (10 contratos, `storage`/`notification_center`/`integration`
adicionados) passaram limpos no repositório inteiro. A suíte fecha em **168 passed, 0 failed** —
detalhe completo em
[`transversais/README.md`](./transversais/README.md#achados-deste-lote-sprint-11-lote-10).
D412–D417 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 9 — Mobile/App Motorista (concluído)

Bounded context `mobile` — Sessão Mobile (D407, chave primária compartilhada com `Sessão`/
`identity_access`), Dispositivo Mobile, Fila de Sincronização (D410, offline), Registro de
Sincronização, Assinatura Digital. Princípio central confirmado pelo usuário: o app é **cliente do
domínio**, nunca um domínio paralelo — os cinco comandos de Viagem (`accept`/`start`/`interromper`/
`retomar`/`finish`), `RegisterOccurrence`, `CreateDelivery` e `RegisterProofOfDelivery` são chamados
a partir de `modules/mobile` pelas mesmas classes `Handler` já usadas pelos endpoints Web de
`freight`, tanto no caminho direto (`/mobile/trips/{id}/commands/X`) quanto na fila offline
(`/mobile/sync`, tabela de despacho única `SYNC_COMMAND_HANDLERS`, D410) — nunca duas
implementações. Documentação de implementação em [`mobile/README.md`](./mobile/README.md) (e os 2
documentos que ele indexa).

Escopo confirmado pelo usuário: exatamente as 5 entidades já congeladas em
`dictionary/009-app_motorista.md`/`relational/009-app_motorista.md`, reusando `identity_access`/
`freight`/`tracking` já existentes — sem Checklist físico (D305, ainda documentação-only). Tenant e
Motorista de uma requisição mobile vêm sempre da Sessão autenticada, nunca do corpo (D408 resolve o
login por CPF+Placa entre tenants, já que nenhum dos dois é globalmente único como `email`, D208).
Aplicou o D352 às 5 entidades mais as **oito auditorias** que o usuário pediu explicitamente:
idempotência via `identificador_local_unico`, ordem de processamento por `sequencia_local` (nunca
pela ordem de chegada HTTP), conflito registrado como `CONFLITO` com o payload original preservado
(nunca sobrescrito, D139), independência total entre Sessão e Dispositivo (D132) nas duas direções,
tenant/identidade sempre da Sessão, RBAC reaproveitando os códigos de domínio existentes (nunca uma
segunda autorização operacional), `push_token` como metadata pura de Dispositivo, e fotos/canhotos/
assinaturas sempre por `arquivo_id` (nunca base64/binário) — mais a auditoria adicional proposta
pelo próprio usuário: o mesmo comando via endpoint Web direto e via sincronização Mobile produz a
mesma transição e o mesmo efeito de domínio (validação concreta de D303).

`alembic upgrade head` criou 5 tabelas novas na primeira tentativa, sem nenhum ajuste manual de
constraint (diferente dos Lotes 7/8, cujas tabelas particionadas/PostGIS sempre exigiam correção
pós-autogenerate) — nenhuma delas é particionada. Encontrou um gap real de segurança/correção antes
de qualquer teste rodar (login não checava o `status` do Dispositivo, auto-detectado desenhando o
cenário da Auditoria #4) e um achado de dependência transitiva só visível rodando contra o Postgres
real: `/mobile/trips/{id}/commands/start` herda, via o mesmo `DispatchTripHandler` do endpoint Web,
a criação automática de CT-e do Lote 7 (D396) — um tenant sem `FiscalConfiguration` rejeita o
comando com `FISCAL_CONFIG_NOT_FOUND`, prova de que reusar o `Handler` exato também importa os
efeitos colaterais reais dele, não só a transição de estado. `ruff`/`mypy --strict` (1236 arquivos)/
`lint-imports` (10 contratos, incluindo o carve-out documentado de `modules.mobile` → `modules.
freight`) passaram limpos no repositório inteiro. A suíte fecha em **156 passed, 0 failed** (144
acumulados + 12 novos de Mobile) — detalhe completo em
[`mobile/README.md`](./mobile/README.md#achados-deste-lote-sprint-11-lote-9). D407–D411 registradas
em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 8 — Rastreamento (concluído)

Bounded context `tracking` — Provedor/Equipamento de Rastreamento (D128), Origem de Localização
(Platform Reference Data), Posição de Veículo (Time Series + PostGIS), Leitura de Telemetria (Time
Series EAV, D120), Heartbeat (Time Series técnico, exceção D191), Cerca Eletrônica (PostGIS,
CIRCULO/POLIGONO), Configuração de Limite de Velocidade e Evento de Rastreamento (derivado,
particionado). Primeiro lote geoespacial do backend — PostGIS 3.6.2 instalado no Postgres portátil
antes de qualquer código (não estava disponível). Documentação de implementação em
[`tracking/README.md`](./tracking/README.md) (e os 3 documentos que ele indexa).

`048`-`051` são somente leitura (D286) — sem contrato de ingestão pública definido ainda —, então
`TrackingIngestion` (D402, mesmo espírito de `TripInternalTransitions`/`FiscalInternalTransitions`)
é como dado bruto entra nesta lote: nunca alcançável por HTTP, só chamada diretamente. Roda as duas
únicas detecções com regra concreta e congelada em algum documento (Geofence via PostGIS, Excesso de
Velocidade via `SpeedLimitConfig`) — Parada/Desvio de Rota deliberadamente sem gatilho automático
(limiares não documentados). Central: D116/D285 ("Tracking observa, nunca decide o estado
operacional") — mecanizado por um contrato `import-linter` inteiro (D405) que impede `modules.
tracking` de importar qualquer coisa de `modules.freight`, primeiro contrato módulo-inteiro-contra-
módulo-inteiro do projeto. Aplicou o D352 aos agregados com CRUD real mais as sete auditorias que o
usuário pediu explicitamente: imutabilidade de Time Series, três timestamps distintos (+ exceção do
Heartbeat), geofence real via PostGIS (índice GiST confirmado usável via `EXPLAIN`), telemetria EAV,
evento derivado nunca mutando Viagem, equipamento único PRINCIPAL testado direto contra o banco, e
paginação por cursor sem duplicação/perda. `alembic upgrade head` criou 9 tabelas novas — cinco
achados reais de implementação encontrados rodando contra PostGIS de verdade (nunca em mock):
`spatial_ref_sys` como novo tipo de falso-positivo de autogenerate, `ST_X`/`ST_Y` exigindo cast
`::geometry` explícito (não existem para `geography`), `ST_DWithin`/`ST_Covers` exigindo o literal de
ponto tipado via `ST_GeogFromText` (senão asyncpg infere `VARCHAR` e a função não resolve),
`recebido_em` precisando entrar na constraint única de `heartbeats` (mesma família D201/D202/Lote 7),
e `POST`/`PATCH`/`DELETE` num path com `GET` já registrado devolvendo `405`, não `404`. `ruff`/
`mypy --strict`/`lint-imports` (10 contratos) passaram limpos. A suíte fecha em **144 passed, 0
failed** (127 acumulados + 17 novos de Rastreamento) — detalhe completo em
[`tracking/README.md`](./tracking/README.md#achados-deste-lote-sprint-11-lote-8). D402–D406
registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 7 — Fiscal (concluído)

Bounded context `documents` — CT-e (máquina de 8 estados, a mais granular do sistema), MDF-e
(consolida um ou mais CT-e via `mdfes_ctes`), CIOT (motorista autônomo), Carta de Correção e NF-e
Referenciada (sub-recursos de CT-e), Evento Fiscal (log técnico particionado, `eventos_fiscais`) e
Configuração Fiscal do Tenant (fonte única de numeração, D110). Escopo confirmado pelo usuário:
exatamente os 5 agregados já congelados, sem nenhuma mudança estrutural na OpenAPI/modelo
relacional — primeiro lote sob essa restrição explícita. Documentação de implementação em
[`fiscal/README.md`](./fiscal/README.md) (e os 6 documentos que ele indexa).

CT-e nasce automaticamente ao despachar a Viagem (`freight`→`documents`, D396) — sem `POST /ctes`
manual, mesmo formato "consumidor futuro de evento síncrono" já usado por `financial`→`freight`
(D390, Lote 6), aqui pela primeira vez na direção oposta. `FiscalInternalTransitions` (D397, mesmo
espírito de `TripInternalTransitions`/D376) simula as duas respostas genuinamente assíncronas da
SEFAZ (CT-e `AUTORIZADO`/`DENEGADO`, MDF-e `AUTORIZADO`) — CIOT não precisa disso, `commands/
register` já é síncrono de verdade. Aplicou o D352 aos 7 agregados mais as cinco auditorias que o
usuário pediu explicitamente: idempotência de protocolo SEFAZ/ANTT, XML sempre como referência
(nunca inline), cardinalidade exata de `*_status_history` por transição, numeração congelada da
Configuração Fiscal mesmo após ela mudar, e reprocessamento de evento nunca duplicando `eventos_
fiscais`. `alembic upgrade head` criou 11 tabelas novas sem bug de DDL não previsto — só dois
ajustes manuais já esperados (partição de `eventos_fiscais`, coluna de partição na constraint
única) — e `ruff`/`mypy --strict`/`lint-imports` passaram limpos na primeira execução. A própria
suíte de integração encontrou e corrigiu dois bugs de implementação reais antes do fechamento
(D401) — nenhum achado de arquitetura, exatamente o tipo de decisão que o usuário pediu para este
lote em diante. A suíte fecha em **127 passed, 0 failed** (111 acumulados + 16 novos de Fiscal) —
detalhe completo em [`fiscal/README.md`](./fiscal/README.md#achados-deste-lote-sprint-11-lote-7).
D396–D401 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 6 — Financeiro (concluído)

Bounded context `financial` — o dinheiro do tenant com seus próprios clientes/fornecedores, nunca
`subscription`/`billing` (D272, o SaaS da própria plataforma). 6 agregados novos — `ChartOfAccounts`
(Plano de Contas, com detecção de ciclo), `BankAccount` (Conta Bancária, saldo sempre derivado,
D263), `AccountsPayable` (Contas a Pagar, alçada automática + Rateio de Despesa alimentando `Trip.
custo_realizado`), `Invoice` (Fatura, precondição real de Canhoto+CT-e via leitura cross-module),
`AccountsReceivable` (Contas a Receber, sub-recurso de Fatura), `FinancialReversal` (Estorno,
mecanismo único de correção pós-fato) — mais `GET /viagens/{id}/financeiro`, que vive em
`modules/freight/` (D389, ownership segue o domínio, não o tema do lote). Escopo confirmado
explicitamente pelo usuário: exclusivamente o bounded context financeiro do tenant, sem Billing da
plataforma (D272), sem Conciliação Bancária/Posição de Caixa (D385, fora da lista de Agregados do
kickoff). Documentação de implementação em [`financeiro/README.md`](./financeiro/README.md) (e os 6
documentos que ele indexa).

Aplicou o D352 aos 6 agregados, mais as quatro auditorias que o usuário pediu explicitamente antes
do fechamento: prova por teste de que `Trip.custo_realizado` é sempre derivado por agregação de
Rateio de Despesa, nunca editável diretamente; prova de que toda mudança de status de Conta a
Pagar/Receber (incluindo a derivada `LANCADA→AGUARDANDO_APROVACAO/APROVADA`) grava exatamente uma
linha em `*_status_history`; prova de que um Estorno nunca reverte o status original do lançamento
alvo; prova de que `GET /viagens/{id}/financeiro` mascara `predicted_*`/`actual_*`/`margin`/
`deviation` de forma independente conforme três permissões distintas (D267-style, primeiro uso
significativo neste backend). `alembic upgrade head` criou 8 tabelas novas contra o Postgres
portátil sem nenhum bug de DDL — nenhuma coluna `GENERATED` nova neste lote, então o bug de mapeamento
`Computed(...)` do Lote 5 (D382) não se repetiu; `ruff`/`mypy --strict`/`lint-imports` passaram
limpos na primeira execução. Encontrou um achado real de implementação (D395: a alçada de Contas a
Pagar deriva instantaneamente na criação, deixando `LANCADA` inalcançável via HTTP — identificado
por análise, não por teste falhando) e estendeu pela primeira vez o padrão "consumidor futuro de
evento síncrono" (D247/D375) de cross-*layer* para cross-*module* (D390: `financial` chama
`freight.application.TripInternalTransitions` diretamente). A suíte fecha em **111 passed, 0
failed** (93 acumulados + 18 novos de Financeiro) — detalhe completo em
[`financeiro/README.md`](./financeiro/README.md#achados-deste-lote-sprint-11-lote-6).
D384–D395 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 5 — Operação/Viagens (concluído)

O core domain do sistema: agregado `Trip` (Viagem) — as três dimensões de status
(Operacional/Fiscal/Financeiro, D020) mais o status composto `ENCERRADA` (D019, coluna `GENERATED`
no banco), Snapshots (D038/D071/D073), `TripAllocation` (D188, pacote atômico Motorista+Veículo+
Implemento) — e suas entidades internas `Delivery`/`DeliveryWindow`/`ProofOfDelivery` (multi-drop
real, nunca `entrega1`/`entrega2`) e `Occurrence` (genérica por design, D076), mais a Timeline
(Read Model, sempre consulta, nunca tabela própria, D187). Escopo confirmado pelo usuário:
exclusivamente o agregado Viagem, sem Cotação/Contrato de Frete/Tabela de Preço (próximo core
domain) nem Coleta/Romaneio (sem endpoint neste lote). Documentação de implementação em
[`operacao/README.md`](./operacao/README.md) (e os 4 documentos que ele indexa).

Aplicou o D352 ao agregado e suas entidades internas, mais duas auditorias que o usuário pediu
explicitamente antes do fechamento: prova por teste de que `encerrada` é `GENERATED` e a aplicação
nunca escreve nela (incluindo uma tentativa de `UPDATE` direto via SQL falhando com o erro nativo
do Postgres), e prova por teste de que os Snapshots (`cliente_snapshot`/`nome_motorista_snapshot`/
`placa_veiculo_snapshot`) nunca ressincronizam mesmo depois que Cliente/Motorista mudam via seus
próprios módulos. `alembic upgrade head` criou 9 tabelas novas contra o Postgres portátil sem
nenhum bug de DDL novo (lições dos Lotes 2/4 sobre autogenerate/partições reaplicadas
proativamente) — encontrou, porém, o primeiro bug real de mapeamento ORM do projeto (D382:
colunas `GENERATED STORED` precisam de `sqlalchemy.Computed(...)`, não um `Mapped[...]` comum, ou
o ORM tenta gravá-las e o Postgres rejeita) e um bug pré-existente na suíte de testes desde o Lote
2, só agora exposto (D383). A suíte fecha em **93 passed, 0 failed** (78 acumulados + 15 novos de
Operação) — detalhe completo em
[`operacao/README.md`](./operacao/README.md#achados-deste-lote-sprint-11-lote-5).
D369–D383 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 4 — Frota (concluído)

Primeiro bounded context de negócio depois de Cadastros, escolhido por dependência real: `Viagem`
(Lote 5, Operação) referencia `Veículo Tracionador`/`Implemento` diretamente. 5 agregados —
`Veículo Tracionador` (+ `Ficha Técnica`, `Documento do Veículo`, `Categoria de Veículo`),
`Implemento`, `Composição Veicular`, `Leitura de Hodômetro` (primeira Time Series do projeto,
paginação por cursor), `Disponibilidade do Veículo` (primeiro Read Model somente leitura, populado
exclusivamente por um Projector de eventos, nunca por HTTP). Tudo em `modules/fleet/` — RBAC
`fleet.*` já atribuía as 10 entidades a um único bounded context, sem reconciliação de módulo como em
Cadastros (D353). Documentação de implementação em [`frota/README.md`](./frota/README.md) (e os 5
documentos que ele indexa).

Aplicou o D352 aos 5 agregados, mais duas auditorias que o usuário pediu explicitamente antes do
fechamento: prova por teste de que `disponibilidade_veiculo` não tem nenhum caminho de escrita HTTP,
e prova por teste (não só pelo índice único parcial físico) de que nunca existem duas Composições
Veiculares vigentes para o mesmo veículo. `alembic upgrade head` criou 9 tabelas novas contra o
Postgres portátil sem nenhum bug de DDL novo — as lições dos Lotes 2/3 (D346/D357/D360) foram
aplicadas proativamente desde o primeiro rascunho, não descobertas por uma falha. A suíte fecha em
**78 passed, 0 failed** (58 acumulados + 10 novos de Frota) — detalhe completo em
[`frota/README.md`](./frota/README.md#achados-deste-lote-sprint-11-lote-4).
D361–D368 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 3 — Cadastros (concluído)

Primeiros 5 bounded contexts de negócio com código real além de `identity_access`/`tenancy`:
`Cliente`/`Contato do Cliente` (`crm`), `Fornecedor` (`maintenance`), `Motorista`/`Documento do
Motorista` (`drivers`), `Funcionário` (novo agregado em `identity_access`), `Centro de Custo`
(`financial`) — mais `Endereço`, um componente compartilhado novo (`apps/api/src/shared/addresses/`,
D354) usado por `crm`/`maintenance`. "Cadastros" é só o nome do lote — `RBAC_MATRIX.md` já atribuía
cada agregado a um bounded context real e existente, então nenhum `modules/cadastros/` foi criado
(D353, confirmado com o usuário antes do código). Documentação de implementação em
[`cadastros/README.md`](./cadastros/README.md) (e os 6 documentos que ele indexa).

Aplicou o **Critério de Definição de Pronto (D352)** definido pelo usuário ao fechar o Lote 2 —
migration real + Repository testado + Application testado + E2E via HTTP + auditoria/isolamento —
a cada um dos 5 agregados. `alembic upgrade head` criou as 8 tabelas novas contra o Postgres
portátil; a suíte fecha em **68 passed, 0 failed** (48 unitários + 20 de integração, todos contra o
banco real). Encontrou e corrigiu 5 bugs/gaps reais (D356–D360), incluindo um erro de FK ausente
repetido em 7 dos 8 models novos e uma regra de negócio (`ADDRESS_PRINCIPAL_ALREADY_EXISTS`) que
nunca convertia a exceção do banco em `409` por causa de onde exatamente o `flush()` acontece —
detalhe completo em [`cadastros/README.md`](./cadastros/README.md#achados-deste-lote-sprint-11-lote-3).
D352–D360 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 2 — Core/Identity/Tenancy (concluído)

Primeiro bounded context com código de negócio real: `Tenant`, `Usuário`, `Papel`, `Permissão`,
`Sessão de Acesso`, `AuthorizationService`, fluxo completo `POST /auth/login → JWT → GET /auth/me →
endpoint protegido por RBAC`. Implementa `001-authentication.md` a `005-permissions.md` do contrato
já congelado, sobre `modules/tenancy/` e `modules/identity_access/` (nunca `auth/`/`users/`/
`roles/`/`permissions/` como bounded contexts separados). Documentação de implementação em
[`core/README.md`](./core/README.md) (e os 4 documentos que ele indexa:
`TENANCY_IMPLEMENTATION.md`/`IDENTITY_IMPLEMENTATION.md`/`AUTHORIZATION_IMPLEMENTATION.md`/
`SESSION_IMPLEMENTATION.md`).

Diferente do Lote 1, este lote **exigiu** validação com PostgreSQL real para o fechamento (não
opcional) — resolvido com um PostgreSQL 16 portátil isolado (porta 5433, sem tocar num
`postgres.exe` alheio ao projeto já rodando na porta padrão). `alembic upgrade head` criou as 8
tabelas reais; a suíte de testes (48 unitários do Lote 1 + 10 de integração novos, todos contra o
banco real) fecha em **59 passed, 0 failed**, cobrindo os 8 cenários exigidos pelo usuário (Tenant
Isolation, RBAC, Role único, Roles múltiplos, Soft Delete, Session Revocation, JWT, Auditoria).
Encontrou e corrigiu 7 bugs reais (D345–D351) — detalhe completo em
[`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md#sprint-11-lote-2--coreidentitytenancy-validação-com-postgresql-real).
D338–D351 registradas em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Lote 1.1 — Reconciliação do scaffold `modules/` (concluído)

Antes de tocar em qualquer bounded context real: `apps/api/src/modules/` tinha 30 pastas da Fase 0,
só 25 com lastro real em Domain/Dictionary/Relational/RBAC/OpenAPI (D334). Removidas `landing/`,
`marketplace/`, `telemetry/`, `workflow/` (scaffold puro, sem código, sem referência — D337);
`notifications/` reclassificada para `core/notification_delivery/` (mecanismo de entrega,
infraestrutura, nunca um segundo bounded context concorrendo com `notification_center`, D336).
Detalhe completo, incluindo o raciocínio por pasta, em
[`BACKEND_ARCHITECTURE.md`](./BACKEND_ARCHITECTURE.md#reconciliação-do-scaffold-modules--sprint-11-lote-11-concluída).
D334–D337 registradas com a redação exata do usuário.

## Lote 1 — Backend Foundation (concluído)

Infraestrutura técnica comum a todo bounded context — nenhuma regra de negócio, nenhum model das
133+ tabelas, nenhum endpoint fora dos técnicos (`/health*`).

| Documento | Conteúdo |
|---|---|
| [`BACKEND_ARCHITECTURE.md`](./BACKEND_ARCHITECTURE.md) | Visão geral, stack confirmada, estrutura real de `src/`, D332/D333, reconciliação `modules/` vs. 25 bounded contexts |
| [`DOMAIN_LAYER.md`](./DOMAIN_LAYER.md) | `shared_kernel/domain/` — `BaseEntity`/`BaseAggregateRoot`/`BaseValueObject`/`DomainEvent`/`Result`/`Specification`/`Repository`/`AuthenticatedActor` |
| [`APPLICATION_LAYER.md`](./APPLICATION_LAYER.md) | `shared_kernel/application/` — `Command`/`Query`/`InMemoryCommandBus`/`InMemoryQueryBus`/`EventBus` (porta), fluxo típico de um Command |
| [`INFRASTRUCTURE_LAYER.md`](./INFRASTRUCTURE_LAYER.md) | `core/` inteiro — config, database/UoW, cache, messaging, storage, security, multitenancy, observability, exceptions |
| [`INTERFACES_LAYER.md`](./INTERFACES_LAYER.md) | `interfaces/` — composition root, health router, `RequestContextMiddleware`, `get_current_actor` |
| [`DEPENDENCY_RULES.md`](./DEPENDENCY_RULES.md) | A Regra de Dependência aplicada mecanicamente via `import-linter` — 4 contratos ativos, prova de que o gate barra violação real |
| [`TRANSACTION_MODEL.md`](./TRANSACTION_MODEL.md) | `UnitOfWork`, ordem commit→pull_events→publish, conexões lazy vs. eager, pool |
| [`EVENT_BUS.md`](./EVENT_BUS.md) | `RabbitMQEventBus` — exchange único `domain_events`, routing key = nome do evento, serialização |
| [`ERROR_HANDLING.md`](./ERROR_HANDLING.md) | 8 classes de exceção (7 pedidas + `AuthenticationError`, achado contra `ERROR_MODEL.md`), 3 handlers FastAPI, envelope idêntico ao contrato |
| [`OBSERVABILITY.md`](./OBSERVABILITY.md) | Logging JSON estruturado, `request_id`/`correlation_id`, os 3 health checks |
| [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md) | **O que foi executado de verdade** — ruff/mypy/import-linter/pytest, os 2 bugs reais encontrados e corrigidos, o que fica pendente sem Docker |
| [`BACKUP_RESTORE.md`](./BACKUP_RESTORE.md) | `pg_dump` automatizado, retenção, procedimento e teste real de restore (V1 Operational Hardening, gap P0 do Go-Live Audit) |
| [`CI_PIPELINE.md`](./CI_PIPELINE.md) | Barreira mínima de CI — ruff/mypy/import-linter/pytest/typecheck/lint/Playwright antes de qualquer merge (V1 Operational Hardening, gap P0 do Go-Live Audit) |

## Decisões

| Decisão | Resumo |
|---|---|
| D332 | OpenAPI congelada é o contrato do Backend — nenhum endpoint de negócio sem entrada prévia em `openapi.yaml`, salvo infraestrutura explícita (`/health*`) |
| D333 | Backend nunca altera o contrato silenciosamente — achado → decisão → atualização da fonte → propagação → nova versão, nunca editar `openapi.yaml` para o código caber |
| D334 | Scaffold não é arquitetura — uma pasta criada durante a Foundation só representa um bounded context real quando tem correspondência em Domain/Dictionary/Relational/RBAC e/ou OpenAPI conforme sua natureza |
| D335 | Somente bounded contexts reais permanecem em `apps/api/src/modules/` |
| D336 | `notifications` interno não é bounded context de produto — `notification_center` é o bounded context real; o mecanismo de entrega fica em infraestrutura/shared (`core/notification_delivery/`), nunca um segundo bounded context concorrente |
| D337 | Funcionalidades futuras (`landing`/`marketplace`/`telemetry`/`workflow`) não entram em `modules/` enquanto não forem bounded contexts oficiais com escopo aprovado |

Detalhe completo em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Achados do Lote 1

- **`passlib` 1.7.4 × `bcrypt` 5.0.0 incompatíveis** — bug real, não estilístico, encontrado pelos
  próprios testes automatizados antes de qualquer código de negócio existir. Corrigido fixando
  `bcrypt = "^4.0.1"`. Ver `TESTING_STRATEGY.md`.
- **7 erros reais de `mypy --strict`** — genéricos incompletos e uma incompatibilidade real de
  assinatura em `EventBus.subscribe`, nenhum estilístico. Todos corrigidos, nenhum silenciado em
  massa (só 2 `# type: ignore` pontuais, ambos documentados inline, ambos limitações conhecidas de
  stub do Starlette/FastAPI, não erros de fato).
- **`import-linter` provado ativo, não só configurado** — violação real injetada e capturada
  (`core` importando `interfaces`), depois revertida. Ver `DEPENDENCY_RULES.md`.
- **`docker-compose.yml` ganhou o serviço `api`** — antes deste lote, o compose só subia
  infraestrutura (Postgres/Redis/RabbitMQ/MinIO); o pedido do usuário ("PostgreSQL Redis RabbitMQ
  MinIO API devem subir corretamente") exigia a API também no compose. Adicionado com
  `depends_on: condition: service_healthy` nos quatro serviços de infra e um healthcheck próprio
  contra `/health/live`.
- **Discrepância `modules/` vs. bounded contexts congelados, sinalizada no Lote 1, resolvida no
  Lote 1.1**: a árvore de 30 pastas em `apps/api/src/modules/` (Fase 0, anterior ao Domain Model/
  RBAC rigorosos) tinha uma duplicata aparente (`notifications/` vs. `notification_center/`) e
  quatro pastas sem lastro em nenhum dos bounded contexts confirmados
  (`landing`/`marketplace`/`telemetry`/`workflow`) — auditada e reconciliada antes do Lote 2 tocar
  em `modules/`, ver "Lote 1.1" acima.
- **Docker não disponível no ambiente de construção deste lote** — todo o resto foi verificado por
  execução real (ruff/mypy/import-linter/pytest/48 testes); a conectividade real Postgres/Redis/
  RabbitMQ/MinIO e o `docker compose up` completo (incluindo o novo serviço `api`) ficam
  pendentes de confirmação do usuário. Comandos exatos em `TESTING_STRATEGY.md`.

## Como esta pasta cresce

Um lote por vez, mesmo princípio do resto do projeto. Próximo bounded context ainda não definido —
depende da ordem de dependência real entre módulos (`docs/product/DEPENDENCY_MAP.md`), a confirmar
quando o Lote 3 for aberto.
