# TIME_SERIES_IMPLEMENTATION.md — Posição, Telemetria, Heartbeat

Fonte: `dictionary/008-rastreamento.md`, `relational/008-rastreamento.md` (padrão D191),
`048-vehicle-positions.md`, `049-telemetry-readings.md`, `050-heartbeats.md`.

## Padrão único D191

`posicoes_veiculo`/`leituras_telemetria`/`heartbeats` seguem o mesmo esqueleto:
`id`/`tenant_id`/`<entidade>_id`/`capturado_em`/`recebido_em`/`processado_em`, `PARTITION BY RANGE`
mensal, índice `(<entidade>_id, capturado_em)`. Criadas via SQL bruto na migration — mesmo padrão de
`eventos_fiscais`/`viagem_status_history`/`logs_auditoria`/`leituras_hodometro` (D346/D364/D383):
SQLAlchemy autogenerate não expressa particionamento Postgres.

**Exceção documentada**: `heartbeats` particiona por `recebido_em`, não `capturado_em` — heartbeat
pode não informar captura (D124/D125). `capturado_em` é nullable só nesta tabela.

## `VehiclePosition` (`posicoes_veiculo`) — PostGIS

`localizacao GEOGRAPHY(Point, 4326) NOT NULL`, mapeada via `geoalchemy2.Geography` (D404).
Escrita: `ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography`. Leitura: sempre via
`ST_X(localizacao)`/`ST_Y(localizacao)` explícitos na query — nunca desserialização de WKB em
Python (sem `shapely`). Índice `GIST` em `localizacao` (D197) — a Auditoria #3 do usuário
(`EXPLAIN` num filtro geoespacial) prova que o índice é de fato usado.

Sem FK física em `veiculo_tracionador_id`/`equipamento_rastreamento_id` **dentro da partição** —
mesma exceção documentada em `AUTORIZACAO_MODEL.md`... na verdade `AUDIT_MODEL.md`, para
`logs_auditoria`, reaplicada aqui porque a tabela é particionada (Postgres não indexa FK
eficientemente contra muitas partições).

## `TelemetryReading` (`leituras_telemetria`) — EAV (D120)

Uma linha por sensor por instante — `tipo_sensor` (Enum físico fechado, 11 valores hoje) + `valor`
+ `unidade`, nunca uma coluna por sensor. `posicao_veiculo_id` opcional (quando o mesmo pacote trouxe
posição e telemetria juntos). A Auditoria #4 do usuário insere `RPM` e `TEMPERATURA` para o mesmo
`veiculo_id`/`capturado_em` e prova que ambas persistem como linhas distintas, sem colisão de
unicidade nem coluna dedicada.

## `Heartbeat` (`heartbeats`) — técnico, não de negócio (D105)

`protocolo_externo` opcional (D111) — chave de idempotência quando o Provedor oferece; único parcial
`(equipamento_rastreamento_id, protocolo_externo) WHERE protocolo_externo IS NOT NULL`. Nunca vira
notificação/status automaticamente por si só — `PerdaDeSinalDetectada` (evento de negócio) exigiria
um limiar de ausência de sinal que nenhum documento congelado define (`SLA` "a definir"), então não é
implementado nesta lote (D402).

## Imutabilidade (Auditoria #1) e três timestamps (Auditoria #2)

Nenhum router de `VehiclePosition`/`TelemetryReading`/`Heartbeat` expõe `PATCH`/`DELETE` — só `GET`
cursor-paginado (D286/D287). `TrackingIngestion.ingest_position`/`.ingest_telemetry`/`.ingest_heartbeat`
sempre fazem `INSERT`, nunca `UPDATE` — cada leitura nasce com seus três (ou dois, no caso do
Heartbeat) timestamps explícitos, nunca um único `now()` reaproveitado para todos.

## Paginação por cursor (Auditoria #7)

Reaproveita `shared_kernel/application/cursor_pagination.py` (`encode_cursor`/`decode_cursor`,
`(capturado_em, id)` para Posição/Telemetria, `(recebido_em, id)` para Heartbeat) — mesmo padrão já
usado por `odometer_reading`/status-history de Fiscal, primeira vez sob volume genuinamente alto.

## Erros de domínio

`TRACKING_VEHICLE_NOT_FOUND` (404, ao consultar posições/telemetria/heartbeats de um veículo
inexistente/de outro tenant).

## Auditoria e tenant isolation

Todos os três repositórios filtram por `get_current_tenant_id()`. Sem `logs_auditoria` próprio —
dado técnico de alta frequência, mesmo raciocínio de `leituras_hodometro`/`eventos_fiscais`.
