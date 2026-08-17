# GEOFENCE_AND_EVENTS_IMPLEMENTATION.md — Cerca Eletrônica, Configuração de Limite de Velocidade, Evento de Rastreamento, `TrackingIngestion`

Fonte: `dictionary/008-rastreamento.md`, `relational/008-rastreamento.md`, `051-tracking-events.md`,
`052-geofences.md`.

## `Geofence` (`cercas_eletronicas`) — configuração, não histórico (D122/D289)

CRUD completo (`GET`/`POST`/`PATCH`/`DELETE` soft, D219). `tipo_geometria` `CIRCULO` exige
`centro`+`raio_metros`; `POLIGONO` exige `poligono` (≥ 3 pontos) — `ck_cercas_eletronicas_geometria`
validada na aplicação antes do banco (`400` com mensagem clara em vez de deixar a constraint física
estourar como erro genérico). Polígono sempre fechado explicitamente pelo domínio (primeiro ponto
repetido ao final) antes de persistir — requisito da dictionary ("polígono fechado"), não uma regra
nova inventada aqui.

`centro`/`poligono` mapeados via `geoalchemy2.Geography` (D404), índices `GIST` parciais
(`WHERE centro IS NOT NULL`/`WHERE poligono IS NOT NULL`, D197).

`filial_id` nasce sem FK física (D403, mesma natureza de D355) — `Filial` ainda não implementada.

## `SpeedLimitConfig` (`configuracoes_limite_velocidade`)

Cadastro simples — `categoria_veiculo_id` opcional (ausente = padrão do tenant), `limite_kmh > 0`.
Sem `DELETE` — `PATCH status=INATIVA`.

## `TrackingEvent` (`eventos_rastreamento`) — derivado, nunca substitui a leitura bruta (D119/D288)

Uma tabela física, `tipo` discriminando 7 categorias — `position_id`/`geofence_id`/
`speed_limit_config_id` são sempre referências (D288), nunca cópia de dado da origem (só
`valor_detectado`, cópia deliberada só do valor que disparou a detecção, para consulta rápida sem
join). RBAC fragmentado por categoria (D294) — `list_tracking_events` filtra por linha: sem `type`
explícito, retorna só as categorias para as quais o Actor tem permissão; com `type` explícito sem a
permissão correspondente, `403`.

Particionada por `data_hora` (SQL bruto na migration, mesmo padrão D191-family), mas com um único
timestamp — é detectada pelo sistema, não capturada de fonte externa (`relational/008-rastreamento.md`
é explícito: "não segue o padrão D191 de três timestamps").

## `TrackingIngestion` — como um Evento nasce (D402)

`modules/tracking/application/tracking_ingestion.py`, mesma forma de `TripInternalTransitions`/
`FiscalInternalTransitions` — nunca alcançável por HTTP. Dois métodos relevantes além de
`ingest_position`/`ingest_telemetry`/`ingest_heartbeat`:

- **`_detect_geofence_transitions(vehicle_id, ...)`** — depois de inserir uma Posição, compara contra
  toda `Geofence` `ATIVA` do tenant: `ST_DWithin(localizacao, centro, raio_metros)` para `CIRCULO`,
  `ST_Covers(poligono, localizacao)` para `POLIGONO`. Estado anterior = a posição imediatamente
  anterior do mesmo veículo estava dentro/fora da mesma cerca. Transição `fora→dentro` gera
  `ENTROU_GEOFENCE`; `dentro→fora` gera `SAIU_GEOFENCE`. Sem transição, nenhum Evento.
- **`_detect_speed_violation(vehicle_id, ...)`** — depois de `ingest_telemetry` com
  `tipo_sensor=VELOCIDADE`, compara `valor` contra a `SpeedLimitConfig` aplicável (categoria do
  veículo, senão o padrão do tenant); acima do limite gera `EXCESSO_DE_VELOCIDADE` com
  `configuracao_limite_velocidade_id` preenchido. `posicao_veiculo_id` fica `None` neste caso — o
  schema físico de `eventos_rastreamento` não tem `leitura_telemetria_id` (só `posicao_veiculo_id`),
  então uma detecção originada de Telemetria não tem como referenciar sua origem exata; documentado
  aqui como limitação real da DDL congelada, não corrigido por inventar uma coluna nova.

**Deliberadamente não implementado nesta lote**: `PARADA_DETECTADA` (limiar de tempo parado "a
definir", `SLA` de `008-RASTREAMENTO.md`), `DESVIO_DE_ROTA_DETECTADO` (depende do corredor de
`routing`, ainda fundação futura), `IGNICAO_LIGADA`/`IGNICAO_DESLIGADA` (nenhuma regra de transição
documentada além do próprio valor do sensor — o enum existe no banco, mas nenhum documento pede
detecção automática dele). Os quatro `tipo` continuam válidos no Enum físico e na API — só não têm
gatilho automático ainda, mesmo espírito do achado `valor_servico` (D401): não inventar regra sem
documento.

## Auditoria #5 do usuário — evento derivado nunca muta Viagem

`TrackingIngestion` não importa nada de `modules.freight` — nem `TripRepository`, nem
`TripInternalTransitions`. Provado de duas formas: (1) teste de integração cria uma Viagem, dispara
`ingest_position` produzindo um `ENTROU_GEOFENCE`, relê a Viagem e confirma `status_operacional`
idêntico; (2) contrato `import-linter` D405 barra estruturalmente qualquer import futuro de
`modules.freight` a partir de `modules.tracking`, então a garantia não depende só do teste não
esquecer de cobrir um caminho novo.

## Erros de domínio

`TRACKING_GEOFENCE_NOT_FOUND` (404), `TRACKING_GEOFENCE_NAME_ALREADY_EXISTS` (409),
`TRACKING_GEOFENCE_INVALID_GEOMETRY` (400), `TRACKING_GEOFENCE_IN_USE` (422, ao excluir uma cerca
referenciada por `eventos_rastreamento` recentes), `TRACKING_SPEED_LIMIT_CONFIG_NOT_FOUND` (404),
`TRACKING_EVENT_NOT_FOUND` (404).

## Auditoria e tenant isolation

Todos os repositórios filtram por `get_current_tenant_id()`. `Geofence`/`SpeedLimitConfig` (Reference
Data com CRUD humano) geram `logs_auditoria` normalmente; `TrackingEvent` não (é ele mesmo um log de
detecção, mesmo raciocínio de `EventoFiscal`/`eventos_rastreamento` sendo dado técnico derivado).
