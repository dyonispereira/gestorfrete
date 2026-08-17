# CATALOG_IMPLEMENTATION.md — Provedor, Equipamento, Origem de Localização

Fonte: `dictionary/008-rastreamento.md`, `relational/008-rastreamento.md`, `046-tracking-providers.md`,
`047-tracking-devices.md`, `048-vehicle-positions.md` (seção `/tracking/origins`).

## `TrackingProvider` (`provedores_rastreamento`)

Cadastro puro (D291) — `nome` único por tenant, `status` `ATIVO`/`INATIVO`. Sem `DELETE` —
desativação via `PATCH status=INATIVO`, mesmo padrão de `013-cost-centers.md`. Um provedor
`INATIVO` continua referenciado por Equipamentos existentes (D001).

## `TrackingEquipment` (`equipamentos_rastreamento`) — D128

`identificador_serial` único **globalmente** (não por tenant — é dado físico do equipamento, D084:
nunca reutilizado). `tipo_equipamento` (`PRINCIPAL`/`BACKUP`/`CAMERA`/`SENSOR_TEMPERATURA`/`TPMS`/
`OUTRO`) — no máximo um `PRINCIPAL` vigente (`data_fim_vigencia IS NULL`) por veículo, garantido por
`uq_equipamentos_rastreamento_principal_vigente` (índice único parcial), a mesma constraint física
que a Auditoria #6 do usuário testa diretamente.

**Sem troca atômica** (diferente de D248, `023-vehicle-compositions.md`): o cliente encerra a
vigência do `PRINCIPAL` anterior explicitamente (`PATCH .../{id}` com `ends_at`) antes de criar um
novo — `create_tracking_equipment` rejeita com `409 TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS`
quando o veículo já tem um `PRINCIPAL` vigente, nunca fecha a vigência anterior sozinho.

Sem `DELETE` — `status=REMOVIDO` (distinto de `INATIVO`) cobre remoção física do equipamento sem
apagar o registro.

## `LocationOrigin` (`origens_localizacao`) — Platform Reference Data (D046)

Sem `tenant_id` — catálogo compartilhado por toda a plataforma. Lista fechada por convenção de
produto (`nome`: GPS/GSM/Satélite/Wi-Fi/BLE/Manual/API Externa, `SEED_DATA.md` §15), mas a coluna é
`TEXT UNIQUE`, não um Enum físico — "catálogo, não Enum fechado no código, para admitir fontes novas
sem alteração de sistema" (`dictionary/008-rastreamento.md`). Só `GET /tracking/origins` — sem
`POST`/`PATCH`/`DELETE` nesta API pública (exposto apenas para dar sentido ao filtro `?origin=` de
`048-vehicle-positions.md`, D046-style, reaproveitando `tracking.position.view`).

**Seed (D406)**: mesmo precedente já em uso para `permissoes` — helper de teste/bootstrap
(`_seed_location_origins()`), `INSERT ... ON CONFLICT (nome) DO NOTHING`, nunca uma migration de
dados (nenhuma tabela do projeto tem seed real via migration ainda, `SEED_DATA.md` continua
aspiracional nesse ponto para todo o schema, não só aqui).

## Erros de domínio

`TRACKING_PROVIDER_NOT_FOUND` (404), `TRACKING_PROVIDER_NAME_ALREADY_EXISTS` (409),
`TRACKING_EQUIPMENT_NOT_FOUND` (404), `TRACKING_EQUIPMENT_SERIAL_ALREADY_EXISTS` (409),
`TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS` (409), `TRACKING_EQUIPMENT_PROVIDER_NOT_FOUND` (404),
`TRACKING_EQUIPMENT_VEHICLE_NOT_FOUND` (404).

## Auditoria e tenant isolation

`SqlAlchemyTrackingProviderRepository`/`SqlAlchemyTrackingEquipmentRepository` filtram por
`get_current_tenant_id()`. `LocationOrigin` não tem `tenant_id` (Platform Reference Data) — lido sem
filtro de tenant, igual a `permissoes`.
