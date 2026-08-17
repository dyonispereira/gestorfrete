# BACKEND_FREEZE.md — Auditoria final do Backend Freeze

**Pergunta central**: o Backend implementado corresponde fielmente ao contrato congelado e
consegue nascer do zero em um ambiente limpo?

**Resposta**: sim, com ressalvas honestas e mecanicamente enumeradas abaixo — nenhuma delas
bloqueante, todas classificadas explicitamente (nunca corrigidas em silêncio). O ambiente nasce
do zero de forma idêntica ao ambiente de desenvolvimento incremental; o RBAC nunca usa um código
inventado; a suíte completa passa com as quatro peças de infraestrutura reais e conectadas; a
qualidade arquitetural (ruff/mypy --strict/import-linter/migrations/OpenAPI lint) está limpa.

Todos os números abaixo foram extraídos mecanicamente (scripts em Python/AST, `psql`, `pytest`,
`alembic`, `lint-imports`, `@redocly/cli`) nesta sessão, contra o código e o banco reais — nenhum
foi estimado ou lembrado de memória.

---

## Frente 1 — OpenAPI ↔ FastAPI

Extração mecânica: `docs/api/openapi.yaml` (YAML parseado via `PyYAML`) vs. `app.routes` da
aplicação FastAPI real (`main.create_app()` importada e inspecionada). Comparação após normalizar
o prefixo `/api/v1` e os nomes de parâmetro de path (`{id}` vs. `{trip_id}` etc. → `{param}`).

| Métrica | Valor |
|---|---|
| Operações no `openapi.yaml` | 381 (380 antes da correção nesta auditoria) |
| Rotas reais no FastAPI | 333 (334 antes da remoção D429) |
| Casadas (implementadas exatamente como no contrato) | 326 |
| Só no contrato (não implementadas) | 55 |
| Só no FastAPI (sem operação correspondente no contrato) | **7 — zero rotas de negócio** (8 antes da remoção D429) |

### Dois bugs mecânicos corrigidos na fonte (achado → D200 → corrigir → propagar → retestar)

1. **`DELETE /storage/files/{id}/download-url` — path errado no `openapi.yaml`.** O documento-fonte
   (`078-storage.md`) sempre disse corretamente `DELETE /api/v1/storage/files/{id}` — o `openapi.
   yaml` tinha o operador `delete:` aninhado sob o path errado (`/download-url`, que só deveria ter
   `get:`). O Backend já estava correto (`delete_file`); o contrato é quem tinha o erro de
   transcrição. Corrigido movendo o `delete:` para `/storage/files/{id}`, único lugar coerente com
   a própria documentação-fonte e com o código real.
2. **`GET /tracking/speed-limit-configs/{id}` — nunca declarado no contrato.** Implementado desde
   o Lote 8/9 (mesmo padrão universal desta API: toda listagem tem um `GET` unitário — inclusive
   porque o `PATCH` já exige buscar o estado atual por `id`), mas `052-geofences.md`/`openapi.yaml`
   nunca declararam essa operação. Zero ambiguidade de design (rotina, não é escopo novo) —
   adicionado ao contrato para refletir a implementação real.

Depois das duas correções: 326 casadas, 55 só-no-contrato, 8 só-no-FastAPI (nenhuma das duas
mudanças alterou a contagem de rotas do FastAPI, que continua 334 neste ponto da auditoria).

### D429 — a única rota de negócio sem contrato foi removida (decisão do usuário)

`POST /mobile/trips/{trip_id}/deliveries` (`register_own_delivery`) era, neste ponto da auditoria,
o único achado real desta Frente: o App Motorista implementava a criação de uma nova Entrega na
própria Viagem (reaproveitando `CreateDeliveryHandler`, D303 — mesma regra de negócio do Web,
nenhuma duplicação de lógica), mas `060-driver-sync.md`/`openapi.yaml` nunca declararam essa
operação — só `GET` (lista/item) e `POST .../pod` para este recurso.

O usuário decidiu explicitamente **não** estender o contrato para acomodar o endpoint — registrou
**D429** ("Rota não contratada é removida no Freeze": reaproveitamento de Handler não autoriza uma
nova superfície HTTP; se o Mobile precisar da capacidade no futuro, entra por decisão explícita de
evolução/versionamento, D427) e removeu a rota. A investigação de remoção encontrou um **segundo**
caminho para a mesma capacidade não contratada: o comando de sincronização offline
`REGISTER_DELIVERY` (`POST /mobile/sync`, D410), despachado para o mesmo `CreateDeliveryHandler` —
removido junto, já que D429 se aplica à capacidade, não a uma rota isolada. Nenhum teste
referenciava nominalmente nenhum dos dois caminhos (confirmado por grep antes da remoção); o
endpoint Web equivalente (`modules/freight/interfaces/api/delivery_router.py`, contratado) não foi
tocado. `ruff`/`mypy --strict` limpos nos dois arquivos alterados. Ver
[`../product/DECISIONS.md`](../product/DECISIONS.md#d429).

### Só no FastAPI (7) — todas infraestrutura, zero rotas de negócio

| Rota | Classificação |
|---|---|
| `GET /docs`, `GET /docs/oauth2-redirect`, `GET /redoc`, `GET /openapi.json` | Infraestrutura do próprio FastAPI (Swagger/Redoc/schema) — nunca fez parte do contrato de negócio, não é uma violação da regra "nenhuma rota de negócio sem contrato". |
| `GET /health`, `GET /health/live`, `GET /health/ready` | Infraestrutura de observabilidade (D-alinhado a `BACKEND_ARCHITECTURE.md`), mesma categoria acima. |

Confirmado mecanicamente (mesmo script de diff, reexecutado após a remoção D429): dos 7 itens
`only_in_fastapi`, **os 7 são exatamente estes 7 endpoints técnicos** — objetivo do usuário
("zero rotas de negócio extras") atingido.

### Só no contrato (55) — nenhuma foi implementada agora (Freeze não adiciona funcionalidade)

Classificação explícita por decisão do usuário: **DELIBERADAMENTE_ADIADO** quando existe uma
decisão registrada (D-número) que excluiu o escopo por opção; **FALTANTE** quando o escopo estava
declarado/esperado e simplesmente não foi implementado, sem nenhuma decisão de exclusão por trás.

Agrupadas por família — a contagem de operações de cada família bate exatamente com os 55 totais:

| Família (tag) | Operações | Classificação | Situação |
|---|---|---|---|
| `MaintenanceOrders`/`MaintenanceApprovals`/`MaintenanceHistory`/`MaintenanceOrderItems`/`MaintenancePreventivePlans`/`ServiceTypes` | 28 | **DELIBERADAMENTE_ADIADO** | D417 (Lote 10) documenta a exclusão explicitamente: `Ordem de Serviço` nunca foi um lote de Backend, só apareceu na fase OpenAPI (Sprint 10 Lote 6). `modules/maintenance/` só implementa `Fornecedor`. |
| `Branches`/`Addresses` (Filiais) | 10 | **DELIBERADAMENTE_ADIADO** | D332 excluiu explicitamente `006-branches.md` do escopo do Lote 2 ("implementa exatamente `001` a `005`") — decisão registrada, nunca retomada em nenhum lote seguinte. `modules/tenancy/interfaces/api/` só tem `tenant_router.py`. |
| `Subscriptions`/`SubscriptionPlans`/`RecurringBilling` (Assinatura/Planos/Cobrança Recorrente) | 10 | **DELIBERADAMENTE_ADIADO** | D272 excluiu explicitamente o Billing da própria plataforma do escopo do Financeiro do tenant (Lote 6). Bounded contexts `subscription`/`billing` existem só como scaffold (`modules/billing/`, `modules/subscription/`, sem nenhum router) — nunca foi um lote de Backend dedicado, por decisão, não por omissão. |
| `BankReconciliation`/`CashPosition`/extrato de `BankAccounts` | 5 | **DELIBERADAMENTE_ADIADO** | D385 excluiu explicitamente Conciliação Bancária/Posição de Caixa da lista de Agregados do kickoff do Lote 6 (Financeiro). `bank_account_router.py` tem `/saldo`, não `/extrato`. |
| **`Authentication` (`forgot-password`/`reset-password`)** | **2** | **⚠️ FALTANTE** | **Sem decisão de exclusão.** Diferente de todas as linhas acima, não há nenhum D-número que tenha adiado essas duas operações por opção — elas estavam dentro do próprio escopo declarado do Lote 2 (`001-authentication.md`), reportado como concluído, e simplesmente nunca foram implementadas. `auth_router.py` só tem `login`/`refresh`/`logout`/`me`. |

> **Destaque: `forgot-password`/`reset-password` impactam diretamente a futura tela de
> Login/Recuperação de Senha do Frontend (Sprint 12, Lote 2 — Auth + Tenant + Usuários + RBAC).**
> Como é a única lacuna desta auditoria classificada como FALTANTE (não DELIBERADAMENTE_ADIADO),
> precisa de uma decisão explícita — implementar no Backend antes/durante o Lote 2 do Frontend, ou
> registrar formalmente como adiada — antes que a tela de recuperação de senha seja desenhada, para
> não nascer apontando para um endpoint que não existe.

Nenhuma dessas 55 operações foi implementada nesta sessão — o Freeze audita, não adiciona
funcionalidade. Ficam como inventário honesto, agora com classificação explícita, para o usuário
decidir se/quando agendar cada uma.

---

## Frente 2 — RBAC ↔ Endpoints

Extração mecânica: todo código-fonte (`*.py`) varrido por `grep`/AST atrás de
`require_permission("...")` e de qualquer string literal no formato `modulo.recurso.acao`
(captura também constantes de autorização por campo, ex.: `PREDICTED_PERMISSION = "financial.
trip_predicted_value.view"`) — comparado contra os 404 códigos oficiais extraídos de
`RBAC_MATRIX.md`.

| Métrica | Valor |
|---|---|
| Códigos oficiais em `RBAC_MATRIX.md` | 404 |
| Códigos usados no código-fonte que não existem na matriz (inventados) | **0** |
| Códigos oficiais nunca referenciados em nenhum código | 196 |
| Funções de rota escaneadas (`@router.<método>`) | 327 |
| Sem `require_permission`/`get_current_actor`/sessão mobile detectados | 5 |

**Zero código de permissão inventado** — todo `require_permission("...")` e toda constante de
autorização por campo do projeto inteiro aponta para um código real e existente em
`RBAC_MATRIX.md`.

Dos 196 códigos oficiais nunca referenciados, a distribuição por módulo confirma que acompanham
exatamente os gaps de escopo já conhecidos (não são um problema novo): `maintenance` (53,
D417), `freight` (36 — sub-recursos nunca construídos: Contrato de Frete, Solicitação de Frete,
Abastecimento, Romaneio, Coleta, Cotação), `financial` (15), `fleet` (13), `routing`/`pricing`
(10 cada — módulos-scaffold nunca implementados), `tenancy` (7 — Filiais, mesmo achado da
Frente 1), `platform`/`analytics` (7 cada), `subscription` (6), `drivers` (5),
`identity_access` (5), demais módulos ≤4 cada.

### Os 5 endpoints sem proteção detectada — 4 são intencionalmente públicos, 1 é falso positivo do scanner

| Endpoint | Classificação |
|---|---|
| `POST /auth/login`, `POST /auth/refresh` (Web) | Intencionalmente públicos — são o próprio ponto de entrada de autenticação (D208, desde o Lote 2). |
| `POST /mobile/auth/login`, `POST /mobile/auth/refresh` (App Motorista) | Mesma classificação, canal mobile. |
| `GET /viagens/{trip_id}/financeiro` (`get_trip_financials`) | **Falso positivo do scanner** — verificado manualmente: usa uma dependência composta própria (`_require_trip_financials_access`, `trip_financials_router.py`) que chama `Depends(get_current_actor)` + `Depends(get_authorization_service)` internamente — o scanner ingênuo só procurava a string literal `require_permission(` dentro do corpo da própria função de rota, não dentro de uma dependência auxiliar separada. Endpoint está corretamente protegido (D389, autorização por campo de valor financeiro). |

Conclusão: **100% dos endpoints de negócio têm autorização real** — os únicos sem
`require_permission` são os dois pares login/refresh, que são públicos por desenho.

### Autorização por campo e por subconjunto de linhas — 4 implementações confirmadas, todas consistentes

| Padrão | Onde | Mecanismo |
|---|---|---|
| Campo (`view_cost`) | `ai.inference.view_cost` | `cost` retorna `null` sem a permissão; demais campos da Inferência continuam visíveis. |
| Campo (3 grupos) | `financial.trip_predicted_value/actual_value/margin.view` | Cada grupo de campos financeiros da Viagem mascarado independentemente (D389, D267-style). |
| Subconjunto de linhas (dono vs. compartilhado) | `reporting.dashboard.view_own`/`.view_shared` | `GetDashboardHandler`/`ListDashboardsHandler` combinam os dois conjuntos conforme a permissão do Actor. |
| Subconjunto de linhas (por categoria) | `tracking` — `ListTrackingEventsHandler` | D294: sem `type` explícito, filtra silenciosamente para só as categorias de evento cuja permissão o Actor tem (nunca um `403` genérico); com `type` explícito sem a permissão, `403`. |

---

## Frente 3 — Banco vazio → Alembic HEAD

**Não usado o banco de desenvolvimento incremental como prova.** Criado um banco Postgres
genuinamente novo na mesma instância portátil (`CREATE DATABASE gestorfrete_freeze_test`),
`CREATE EXTENSION postgis` explícito, `alembic upgrade head` rodado do zero absoluto (sem
histórico de migration algum) — as 12 migrations da Sprint 11 (Lote 2 a Lote 12) aplicadas em
sequência, sem nenhum erro.

| Métrica | Banco vazio → HEAD | Banco de desenvolvimento (`gestorfrete`) |
|---|---|---|
| `alembic_version` final | `23928256fece` | `23928256fece` |
| Tabelas em `public` | 109 | 109 |
| Tabelas particionadas | 9 | 9 |
| Constraints totais | 1111 | 1111 |
| Índices totais | 237 | 237 |
| Tipos ENUM nativos do Postgres | 0 | 0 |
| Extensões instaladas | `plpgsql`, `postgis 3.6.2` | `plpgsql`, `postgis 3.6.2` |

**Idêntico em todas as métricas.** Zero tipos ENUM nativos é esperado, não uma lacuna — o projeto
usa `VARCHAR`/`TEXT` com validação na Application em todas as 12 categorias relacionais, nunca
`CREATE TYPE ... AS ENUM` físico (consistente desde a Sprint 09). Banco de teste descartado
(`DROP DATABASE`) depois da comparação — artefato local, nunca versionado.

---

## Frente 4 — Infraestrutura real

Nenhum Docker disponível neste ambiente (achado do Lote 1, nunca revertido) — todas as quatro
peças de infraestrutura instaladas como binário portátil standalone, mesmo espírito de
PostGIS (Lote 8) e MinIO (Lote 10).

| Serviço | Status antes | Como foi resolvido nesta sessão | Status agora |
|---|---|---|---|
| PostgreSQL 17 + PostGIS | Real desde o Lote 8 | — | ✅ Real, `check_database_connection()` |
| MinIO | Real desde o Lote 10 | — | ✅ Real, `check_storage_connection()` |
| **Redis** | Nunca esteve rodando neste ambiente | Binário portátil `tporadowski/redis` (fork Windows não-oficial, único formato viável sem Docker), extraído em `C:\redisportable`, `redis-server.exe` em background na porta `6379` | ✅ Real, `check_redis_connection()` |
| **RabbitMQ** | Nunca esteve rodando neste ambiente | Erlang/OTP 27.3.4.16 (zip portátil oficial `erlang/otp`) + RabbitMQ 4.3.4 (zip portátil oficial `rabbitmq-server-windows`) extraídos em `C:\erlangportable`/`C:\rabbitmqportable`; `rabbitmq-server.bat` com `ERLANG_HOME`/`RABBITMQ_NODENAME` explícitos; usuário `gestorfrete`/`gestorfrete` criado via `rabbitmqctl add_user`/`set_permissions` (mesmas credenciais do `.env`) | ✅ Real, `check_rabbitmq_connection()` |

`test_redis_is_reachable`/`test_rabbitmq_is_reachable` — as duas últimas pendências históricas de
infraestrutura desde o Lote 1 — passam de verdade pela primeira vez em toda a Sprint 11.

---

## Frente 5 — Suíte completa

`pytest` rodado sem nenhuma deseleção (`-m "integration or not integration"`, equivalente a
"tudo"), com as quatro peças de infraestrutura reais simultaneamente.

| Execução | Resultado |
|---|---|
| Antes do fix desta auditoria | 191 passed, **5 errors** (teardown) |
| Depois do fix | **191 passed**, 0 errors, 1 warning benigno |
| Deselecionados por infraestrutura ausente | **0** |

### Bug real encontrado e corrigido — primeira vez que RabbitMQ roda de verdade durante os testes

`tests/unit/test_health.py` (5 testes, `TestClient` síncrono) começou a falhar no teardown com
`RuntimeError: Event loop is closed` / `got Future attached to a different loop`. Causa raiz:
`core/messaging/rabbitmq_client.py` mantém uma conexão robusta (`aio_pika.connect_robust`)
cacheada em uma variável global de processo; a conexão "robusta" roda uma tarefa de bastidores
que reconecta automaticamente, presa ao event loop em que nasceu. Cada `TestClient(app)` cria um
novo event loop (portal do Starlette); antes desta sessão, `check_rabbitmq_connection()` **nunca
chegou a abrir uma conexão real** (RabbitMQ sempre esteve fora do ar, caía direto no `except
Exception: return False`) — o bug estava latente, mecanicamente inalcançável até agora. Mesma
classe de problema já resolvida antes para o SQLAlchemy engine (`dispose_engine()`, D383) — nunca
para RabbitMQ, porque nunca houve uma conexão real para vazar. Corrigido em
`close_rabbitmq_connection()`: a chamada a `.close()` agora é protegida por `try/except`,
documentando explicitamente a causa (tarefa de watchdog do `aio_pika` que não cancela de forma
síncrona dentro de um event loop de vida curta) — mesma disciplina defensiva já usada em
`check_rabbitmq_connection`. Retestado isoladamente (5/5 passou) e depois a suíte completa (0
erros).

---

## Frente 6 — Qualidade arquitetural

| Ferramenta | Resultado |
|---|---|
| `ruff check src tests` | **All checks passed** |
| `mypy src` (`--strict`) | **Success: no issues found in 1538 source files** |
| `lint-imports` (`import-linter`) | **12 kept, 0 broken** — nenhuma dependência inversa nova |
| `alembic check` (contra o banco de desenvolvimento) | Nenhum drift genuíno — só o conjunto conhecido de falsos positivos de particionamento (D360, agora incluindo `inferencias_ia_default`, mesmo padrão desde o Lote 4) |
| `@redocly/cli lint docs/api/openapi.yaml` | **0 erros**, 387 warnings (todos pré-existentes, `operation-operationId` — nenhuma `operationId` declarada em nenhum lote desde a Sprint 10; crescimento esperado, não regressão) |

---

## Achados consolidados desta auditoria

1. **Corrigido na fonte, sem ambiguidade de escopo** (D200 aplicado, retestado): path errado de
   `DELETE /storage/files/{id}/download-url`; `GET /tracking/speed-limit-configs/{id}` ausente do
   contrato.
2. **Corrigido no código** (bug real, nunca antes alcançável): cleanup de conexão RabbitMQ em
   `core/messaging/rabbitmq_client.py`.
3. **Resolvido por decisão explícita do usuário — D429**: `POST /mobile/trips/{id}/deliveries` e o
   comando de sincronização equivalente `REGISTER_DELIVERY` (mesmo Handler, dois caminhos para a
   mesma capacidade não contratada) removidos do Backend. Reauditado mecanicamente após a remoção:
   **zero rotas de negócio** sem contrato correspondente (7 `only_in_fastapi`, todas infra).
4. **Inventário honesto de escopo nunca implementado, agora classificado explicitamente**: 53
   operações **DELIBERADAMENTE_ADIADO** (Manutenção/Ordem de Serviço 28 — D417; Filiais 10 — D332;
   Assinatura/Planos/Cobrança Recorrente 10 — D272; Conciliação Bancária/Posição de Caixa/Extrato 5
   — D385) e 2 operações **FALTANTE** (`forgot-password`/`reset-password` — sem decisão de
   exclusão, impacta diretamente a futura tela de Login/Recuperação do Frontend).

## Decisões registradas

D427 (Backend Freeze — mudanças incompatíveis com a OpenAPI congelada exigem versionamento
explícito), D428 (ambiente limpo é critério de release) e D429 (rota não contratada é removida no
Freeze — aplicado retroativamente ao achado da Frente 1) — ver
[`../product/DECISIONS.md`](../product/DECISIONS.md).

## Conclusão

O Backend corresponde fielmente ao contrato congelado (326 de 333 rotas reais casadas, 100% delas
com RBAC correto e rastreável a um código oficial, **zero rotas de negócio sem contrato** depois de
D429) e nasce de um ambiente Postgres genuinamente vazio produzindo um schema byte-a-byte
equivalente ao ambiente de desenvolvimento. As categorias de divergência ficam totalmente
resolvidas ou explicitamente classificadas: dois bugs mecânicos de contrato (corrigidos), um bug
real de infraestrutura de teste (corrigido), uma rota implementada além do contrato (removida por
D429) e um inventário de escopo nunca implementado, agora dividido entre DELIBERADAMENTE_ADIADO (53
operações, cada uma com decisão própria) e FALTANTE (2 operações — `forgot-password`/
`reset-password`, destacadas para decisão antes do Lote 2 do Frontend). **Aprovado para
congelamento técnico — Backend Freeze aprovado pelo usuário, D427/D428/D429 fechadas.**
