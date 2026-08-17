# 025 — Vehicle Availability

Bounded context proprietário: `fleet` (D215). `disponibilidade_veiculo` — Read Model puro (D081),
sujeito a D247.

## D247 — nenhum comando de escrita

```
GET /api/v1/veiculos/disponibilidade
GET /api/v1/veiculos/{id}/disponibilidade
```

**Sem `POST`/`PATCH`/`DELETE`** — confirmado também por RBAC:
`fleet.vehicle.view_availability` é a única permissão relacionada em `RBAC_MATRIX.md` 7.8, não há
`.edit`/`.create` (mesma ausência já vista em `Session`/`TenantContext`, Lote 2 — Read Models nunca
têm verbo de escrita próprio). Fisicamente, `disponibilidade_veiculo` só é populada por
consumidores de evento (`ViagemDespachada`, `ViagemConcluida`, `OrdemServicoAberta`, etc.) — nenhum
Controller escreve nela, então nenhum endpoint pode escrever nela.

**Disponibilidade é projeção, não é fonte de verdade** — todo campo em `VehicleAvailability`
(`fleet-schemas.md`) é `readOnly`. A fonte de verdade real de "onde está o Veículo agora" é a
combinação de `alocacoes_recurso_viagem` (vigente) + o Status Operacional da Viagem vigente
(`014-trips.md`) + Ordens de Serviço abertas (`maintenance`, lote futuro) — esta consulta é só o
resumo já materializado.

## `GET /api/v1/veiculos/disponibilidade`

Lista a disponibilidade de todos os Veículos do tenant — útil para o painel operacional decidir
qual Veículo alocar numa Viagem nova.

**Segurança**: `bearerAuth` + `fleet.vehicle.view_availability`.

**Query parameters**: `page`/`limit`, `status` (`DISPONIVEL`/`EM_VIAGEM`/`EM_MANUTENCAO`/
`INATIVO`).

**Responses**: `200` (`Pagination` de `VehicleAvailability`), `401`, `403`, `500`.

## `GET /api/v1/veiculos/{id}/disponibilidade`

**Segurança**: `fleet.vehicle.view_availability`. **Responses**: `200`
(`VehicleAvailability`), `401`, `403`, `404` — `FLEET_VEHICLE_AVAILABILITY_NOT_FOUND` (Veículo
existe mas a projeção ainda não foi materializada — cenário raro, Veículo recém-criado antes do
primeiro evento consumido), `500`.

## Como este documento cresce

Nenhuma mudança prevista — Read Model puro, sem verbo de escrita, é estável por definição.
