# 020 — Vehicles

Bounded context proprietário: `fleet` (D215).

## Separação por conceito, nunca misturados

| Conceito | Onde vive no schema | Onde vive fisicamente |
|---|---|---|
| Identidade | `Vehicle.identity` (`codigo`/`plate`/`renavam`) | `veiculos_tracionadores` |
| Técnico | Sub-recurso `GET/PATCH /veiculos/{id}/technical-sheet` | `veiculos_tracionadores` (parte) + `fichas_tecnicas_veiculo` |
| Operacional | `Vehicle.operational`, sempre `readOnly` | `disponibilidade_veiculo` (Read Model, `025-vehicle-availability.md`) |
| Rastreamento | `Vehicle.tracking_reference`, só ponteiro (D250) | `tracking` — não consultado aqui neste lote |

## `GET /api/v1/veiculos`

**Segurança**: `bearerAuth` + `fleet.vehicle.view` (ou `.view_own` — Motorista consultando o
veículo da própria Viagem em andamento).

**Query parameters** (D226 — todos correspondem a colunas reais):

| Parâmetro | Coluna |
|---|---|
| `page`, `limit` | Offset — Master Data |
| `search` | `placa`/`fabricante`/`modelo` (`__contains`) |
| `placa` | `placa` (igualdade exata) |
| `status` | `status` |
| `categoria_id` | `categoria_veiculo_id` |
| `fabricante` | `fabricante` |
| `modelo` | `modelo` |
| `ano` | `ano_fabricacao` |

**Sem filtro de disponibilidade/localização aqui** — isso é `025-vehicle-availability.md` e
`tracking` respectivamente, nunca misturado nesta listagem (D250).

**Responses**: `200` (`Pagination` de `Vehicle`), `401`, `403`, `500`.

## `GET /api/v1/veiculos/{id}`

**Segurança**: `fleet.vehicle.view`/`.view_own`. **Responses**: `200` (`Vehicle`), `401`, `403`,
`404` (`FLEET_VEHICLE_NOT_FOUND`), `500`.

## `POST /api/v1/veiculos`

**Segurança**: `fleet.vehicle.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          plate: { type: string }
          renavam: { type: string }
          fabricante: { type: string }
          modelo: { type: string }
          ano_fabricacao: { type: integer }
          categoria_id: { $ref: "components/schemas.md#/UUID" }
          branch_id: { $ref: "components/schemas.md#/UUID" }
        required: [plate, renavam, fabricante, modelo, ano_fabricacao, categoria_id]
```

`operational`/`tracking_reference` nunca aceitos (`readOnly`) — `disponibilidade_veiculo` é
populada por consumidor de evento, nunca por este `POST` (mesmo princípio já em vigor no Modelo
Relacional: "nenhuma rota de API de escrita direta nesta tabela").

**Responses**: `201` (`Vehicle`), `400`, `401`, `403`, `409` (D230 — `FLEET_VEHICLE_PLATE_
ALREADY_EXISTS`/`FLEET_VEHICLE_RENAVAM_ALREADY_EXISTS`), `500`.

## `PATCH /api/v1/veiculos/{id}`

**Segurança**: `fleet.vehicle.edit`. D229 — parcial. Mesmos campos de `POST`, todos opcionais,
mais `status`. **Não altera `technical-sheet`** (sub-recurso próprio, abaixo) nem `operational`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## `DELETE /api/v1/veiculos/{id}`

**D219 — soft delete.** **Segurança**: `fleet.vehicle.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `FLEET_VEHICLE_HAS_ACTIVE_TRIP` (Veículo com
alocação vigente, `alocacoes_recurso_viagem`), `500`.

## `GET /api/v1/veiculos/{id}/technical-sheet`

Sub-resource com RBAC próprio (D225 — tem autorização dedicada em `RBAC_MATRIX.md`, qualifica
como sub-recurso de verdade, não uma seção arbitrária do Vehicle).

**Segurança**: `fleet.vehicle_technical_sheet.view`. **Responses**: `200`
(`VehicleTechnicalSheet`), `401`, `403`, `404` (Veículo existe mas ainda não tem Ficha Técnica
cadastrada), `500`.

## `PATCH /api/v1/veiculos/{id}/technical-sheet`

**Segurança**: `fleet.vehicle_technical_sheet.edit`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          chassis: { type: string }
          engine: { type: string }
          axles: { type: integer }
          tare_weight: { type: string }
          load_capacity: { type: string }
          gross_vehicle_weight: { type: string }
          owner_rntrc: { type: string }
          fuel_type: { type: string, enum: [DIESEL_S10, DIESEL_S500, GNV, ELETRICO] }
```

`chassi`/`renavam`/`ano_fabricacao` são dados permanentes (D082) — a API não bloqueia
tecnicamente a edição (o Modelo Relacional também não), mas toda alteração aqui gera entrada
reforçada em `logs_auditoria` (mesmo nível de rigor de uma ação sensível, D082), nunca uma edição
silenciosa.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` (D230 — `FLEET_CHASSIS_ALREADY_EXISTS`),
`500`.

## Fora de escopo deste lote (não esquecido)

`Seguradora`/`Apólice de Seguro Veicular`/`Licenciamento do Veículo` — tabelas físicas existentes
(`apolices_seguro_veicular`, `licenciamentos_veiculo`, `seguradoras`), com Permissões já em
`RBAC_MATRIX.md` (`fleet.insurance_policy.*`), mas **sem endpoint neste lote** — o pedido explícito
cobriu Veículo/Documentos(genérico)/Implemento/Composição/Hodômetro/Disponibilidade, não essas
três. Mesma disciplina de `015-trip-deliveries.md` (Coleta/Romaneio) — D242, lacuna de dependência
explícita, nunca uma implementação provisória.

## Como este documento cresce

Seguro/Licenciamento entram num lote futuro de Frota — mesmo padrão de sub-recurso com RBAC próprio
já estabelecido aqui para `technical-sheet`.
