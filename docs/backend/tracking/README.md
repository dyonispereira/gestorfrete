# docs/backend/tracking — Sprint 11, Lote 8 (Rastreamento)

Documentação de implementação do bounded context `tracking` — Provedor de Rastreamento, Equipamento
de Rastreamento, Origem de Localização, Posição de Veículo, Leitura de Telemetria, Heartbeat, Cerca
Eletrônica, Configuração de Limite de Velocidade, Evento de Rastreamento. Escopo confirmado pelo
usuário: as 9 entidades já congeladas em `dictionary/008-rastreamento.md`/`relational/008-rastreamento.md`
e os endpoints já congelados em `039-cte.md`... na verdade `046-tracking-providers.md` a
`053-tracking-history.md`. Sem pipeline genérico de ingestão pública — não congelado no contrato
(D286/D402).

| Documento | Cobre |
|---|---|
| [`CATALOG_IMPLEMENTATION.md`](./CATALOG_IMPLEMENTATION.md) | `TrackingProvider`, `TrackingEquipment` (D128), `LocationOrigin` (Platform Reference Data) |
| [`TIME_SERIES_IMPLEMENTATION.md`](./TIME_SERIES_IMPLEMENTATION.md) | `VehiclePosition` (PostGIS), `TelemetryReading` (EAV), `Heartbeat` (D191 + exceção) |
| [`GEOFENCE_AND_EVENTS_IMPLEMENTATION.md`](./GEOFENCE_AND_EVENTS_IMPLEMENTATION.md) | `Geofence`, `SpeedLimitConfig`, `TrackingEvent`, `TrackingIngestion` (D402) |

Tudo em `modules/tracking/` — RBAC `tracking.*` (§7.16), já totalmente presente antes deste lote
(quinta ocorrência de "RBAC preenchido na origem antes do documento de API existir", D293, já feito
em `046`/`047`/`049`/`050`/`052` antes deste lote começar).

## Central: D116/D285 — "Tracking observa. Tracking não decide o estado operacional."

Nenhum código em `modules/tracking` escreve em `modules.freight` — nem em `Trip`, nem em qualquer
outra entidade de outro bounded context. Diferente de `financial`/`documents` (que **escrevem**
`Trip.status_fiscal`/`.status_financeiro` via `TripInternalTransitions`, D390/D398), este módulo é
unidirecional: só lê o necessário (nenhuma leitura cross-module sequer é necessária nesta lote) e só
publica observação. Mecanizado por um contrato `import-linter` inteiro (D405) — não só um teste que
poderia ser esquecido num lote futuro.

## `TrackingIngestion` — como dado bruto entra no sistema (D402)

`048`-`051` são somente leitura (D286) — nenhum `POST` de Posição/Telemetria/Heartbeat/Evento existe
nesta API pública; o contrato de ingestão real (webhook/polling/API do Provedor/queue) ainda não foi
decidido. `TrackingIngestion` (`modules/tracking/application/tracking_ingestion.py`) nasce com a
mesma forma de `TripInternalTransitions`/`FiscalInternalTransitions` (D376/D397) — não é alcançável
por HTTP, só chamado diretamente (testes hoje, pipeline real quando existir). Ver
`GEOFENCE_AND_EVENTS_IMPLEMENTATION.md` para o que ela detecta e, deliberadamente, o que não detecta.

## PostGIS — primeira dependência geoespacial do backend (D404)

A DDL congelada (`localizacao GEOGRAPHY(Point, 4326)`, `centro`/`poligono` em `cercas_eletronicas`)
exige a extensão PostGIS, que não estava instalada no Postgres portátil usado para os testes de
integração de todo lote anterior — instalada nesta lote (PostGIS 3.6.2, bundle oficial OSGeo para
PostgreSQL 16 Windows x64) antes de qualquer código ser escrito, mesma disciplina de nunca escrever
contra uma infraestrutura que não existe de verdade (`TESTING_STRATEGY.md`). Mapeamento ORM via
`geoalchemy2` (D404).

## Critério de Definição de Pronto (D352) + 7 auditorias explícitas do usuário

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation + auditoria
comprovados por teste — mais as sete auditorias pedidas explicitamente antes de fechar o lote:

1. **Imutabilidade de Time Series** — Posição/Telemetria/Heartbeat sem `PATCH`/`DELETE`; uma leitura
   persistida nunca é sobrescrita.
2. **Três timestamps distintos** — `capturado_em`/`recebido_em`/`processado_em` para Posição/
   Telemetria; exceção D191 do Heartbeat (`capturado_em` pode ser `None`, particiona por `recebido_em`).
3. **Geofence real** — ponto dentro/fora de uma Cerca via PostGIS de verdade, índice espacial
   usável, geofence nunca confundida com Evento de Rastreamento.
4. **Telemetria EAV** — dois sensores diferentes (RPM/TEMPERATURA) no mesmo instante sem coluna
   dedicada; `tipo_sensor` é Enum controlado.
5. **Evento derivado nunca muta Viagem** — criar/processar um Evento de Rastreamento e provar que
   `Trip.status_operacional` nunca muda por causa dele.
6. **Equipamento único PRINCIPAL (D128)** — direto contra o banco, não só a regra de aplicação.
7. **Paginação por cursor** — inserir várias leituras, buscar página 1, capturar cursor, buscar
   página 2, garantir zero duplicação/perda.

## Achados deste lote (Sprint 11, Lote 8)

`alembic upgrade head` criou as 9 tabelas novas contra o Postgres portátil já com PostGIS 3.6.2
instalado nesta lote — `provedores_rastreamento`/`equipamentos_rastreamento`/`origens_localizacao`/
`cercas_eletronicas`/`configuracoes_limite_velocidade` via `CREATE TABLE` normal; `posicoes_veiculo`/
`leituras_telemetria`/`heartbeats`/`eventos_rastreamento` via SQL bruto particionado (D191-family,
mesmo padrão de `eventos_fiscais`). `ruff`/`mypy --strict`/`lint-imports` (10 contratos, incluindo o
novo D405) passaram limpos. A suíte fecha em **144 passed, 0 failed** (127 acumulados + 17 novos de
Rastreamento; Redis/RabbitMQ/MinIO continuam fora do ambiente de build — os únicos 3 testes que
falham na suíte completa são exatamente esses, já documentados como limitação de infraestrutura
desde a Sprint 09).

Cinco achados reais de implementação, todos só visíveis rodando contra o Postgres/PostGIS de
verdade, nunca em mock:

1. **`spatial_ref_sys`** — tabela interna do próprio PostGIS (criada por `CREATE EXTENSION postgis`,
   fora do `Base.metadata` da aplicação). `alembic --autogenerate` propõe removê-la, mesma classe de
   falso-positivo dos `_default` de tabela particionada (D360), mas por um motivo novo: não é uma
   partição órfã, é uma tabela de sistema de uma extensão. Nunca aplicado.
2. **`ST_X`/`ST_Y` não existem para `geography`** — só para `geometry`; toda leitura de coordenada
   precisa de `CAST(coluna AS geometry)` explícito primeiro (`sqlalchemy_vehicle_position_repository.py`/
   `sqlalchemy_geofence_repository.py`). Confirmado rodando a função direto contra o Postgres antes
   de escrever qualquer repositório (`SELECT ST_X('...'::geography)` → erro; com `::geometry` →
   funciona).
3. **`ST_DWithin`/`ST_Covers` exigem o segundo argumento explicitamente tipado como `geography`** —
   passar um literal Python `str` faz o asyncpg preparar o parâmetro como `VARCHAR`, e
   `ST_DWithin(geography, varchar, numeric)` não existe como sobrecarga (`UndefinedFunctionError`,
   só apareceu na primeira execução real da Auditoria #3). Corrigido envolvendo o literal em
   `func.ST_GeogFromText(...)` antes de usá-lo como argumento.
4. **`uq_heartbeats_equipamento_protocolo` precisou incluir `recebido_em`** — mesma família de achado
   D201/D202 (Sprint 09) e do `uq_eventos_fiscais_documento_protocolo` (Lote 7): Postgres exige que
   toda constraint `UNIQUE` de tabela particionada inclua a coluna de partição. `TrackingIngestion.
   ingest_heartbeat` já verifica `exists_with_protocol` antes de inserir; a constraint é a segunda
   camada de defesa.
5. **`POST`/`PATCH`/`DELETE` num path que só tem `GET` registrado devolve `405`, não `404`** —
   Starlette resolve o path primeiro (rota existe) e só depois checa o método; `404` é reservado a
   paths sem nenhuma rota casando. A Auditoria #1 original assumia `404` para o `POST` de
   `/vehicles/{id}/tracking/positions` (mesmo path do `GET`) e precisou ser corrigida para `405` —
   `PATCH`/`DELETE` em `/positions/{id}` (path que não existe, sem segmento de ID na rota real)
   continuam `404` corretamente.

As sete auditorias explícitas do usuário foram todas verificadas por teste real contra HTTP +
Postgres/PostGIS (`tests/integration/test_tracking_flow.py`):

1. **Imutabilidade de Time Series** — `TestTimeSeriesImmutabilityAudit`: nenhum `PATCH`/`DELETE`/
   `POST` de dado bruto existe; duas posições inseridas em sequência para o mesmo veículo permanecem
   ambas recuperáveis, sem sobrescrita.
2. **Três timestamps** — `TestThreeTimestampsAudit`: `captured_at`/`received_at`/`processed_at`
   estritamente crescentes e distintos para Posição; Heartbeat aceita `captured_at=None` (exceção
   D191).
3. **Geofence real** — `TestGeofenceAudit`: `CIRCULO` (`ST_DWithin`) e `POLIGONO` (`ST_Covers`) reais,
   `ENTROU_GEOFENCE`/`SAIU_GEOFENCE` gerados corretamente; índice GiST confirmado em `pg_indexes` e
   seu uso comprovado via `EXPLAIN` com `enable_seqscan=off` (a partição física herda o nome do
   índice, `posicoes_veiculo_default_localizacao_idx` — achado documentado no teste).
4. **Telemetria EAV** — `TestTelemetryEavAudit`: `RPM` e `TEMPERATURA` no mesmo `capturado_em`
   persistem como duas linhas distintas; `SensorType("SENSOR_INVENTADO_LIVRE")` levanta `ValueError`
   (Enum controlado, D120 — nunca texto livre no sentido do domínio, mesmo padrão já em uso em todo
   o resto do schema, ver "Como este documento cresce" abaixo).
5. **Evento derivado nunca muta Viagem** — `TestTrackingEventNeverMutatesTripAudit`: Viagem criada e
   com veículo alocado, evento `ENTROU_GEOFENCE` real gerado para esse mesmo veículo,
   `status.operational` da Viagem permanece idêntico antes/depois — provado tanto pelo teste quanto
   pelo contrato `import-linter` D405 (`modules.tracking` não importa `modules.freight`).
6. **Equipamento único PRINCIPAL (D128)** — `TestSinglePrincipalEquipmentAudit`: rejeição via API
   (`409`) e, principalmente, `INSERT` bruto via SQL direto no banco também rejeitado pela constraint
   física `uq_equipamentos_rastreamento_principal_vigente`.
7. **Paginação por cursor** — `TestCursorPaginationAudit`: 5 posições inseridas, 3 páginas (`limit=2`),
   união exata dos IDs recuperados igual ao conjunto inserido, zero duplicação, `has_more` correto em
   cada página.

## Enum "controlado" — mesma simplificação já em uso em todo o schema

A DDL congelada declara `CREATE TYPE ... ENUM` para `tipo_equipamento`/`tipo_sensor`/
`tipo_geometria`/`tipo`/`severidade`, mas — igual a **toda** tabela de **todo** lote anterior deste
projeto (nenhuma migration já escrita usa um Postgres `ENUM` físico) — as colunas nascem `VARCHAR`
com validação no domínio (`StrEnum` Python). "Controlado, nunca texto livre" (Auditoria #4) é provado
no nível de aplicação (`SensorType(...)` rejeita valores desconhecidos), não por um tipo físico —
consistente com o padrão já estabelecido, não uma exceção nova criada aqui.

## Decisões

D402–D406 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: Mobile/App Motorista — reaproveita
Operação, Storage, autenticação e sincronização offline já especificadas.
