# 024 — Odometer Readings

Bounded context proprietário: `fleet` (D215). `leituras_hodometro` — Time Series/Histórica
(D037/D050), sujeita a D191 (padrão físico) e D246 (somente leitura na API).

## D246 — nunca editável, nunca excluível

```
GET  /api/v1/veiculos/{id}/odometro/leituras
POST /api/v1/veiculos/{id}/odometro/leituras
```

**Sem `PATCH`, sem `DELETE`** — confirmado também por RBAC: `RBAC_MATRIX.md` 7.8 só tem
`fleet.odometer_reading.view`/`.create`. Uma leitura errada não é corrigida, é superada por uma
leitura nova e correta — mesmo princípio de toda tabela `*_status_history`/Time Series já
estabelecido desde a Sprint 09 (D001/D017/D018 aplicados aqui).

## `GET /api/v1/veiculos/{id}/odometro/leituras`

**Cursor pagination**, não Offset — `leituras_hodometro` é particionada mensalmente (D179),
Categoria Física Time Series (`TABLES.md`), mesma regra de `PAGINATION.md` já aplicada em
`019-trip-timeline.md`.

**Segurança**: `bearerAuth` + `fleet.odometer_reading.view`.

**Query parameters**: `cursor`, `limit`, `origem` (`origin`), `data_hora__gte`/`__lte`
(`FILTERING_SORTING.md`).

**Responses**: `200` (coleção cursor-paginada de `OdometerReading`, `fleet-schemas.md`), `401`,
`403`, `404`, `500`.

## `POST /api/v1/veiculos/{id}/odometro/leituras`

**Segurança**: `fleet.odometer_reading.create` (Escopo inclui Motorista via app — marcado ● em
`RBAC_MATRIX.md`).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          value_km: { type: string }
          origin: { type: string, enum: [ABASTECIMENTO, CHECKLIST, MANUAL, TELEMETRIA] }
          trip_id: { $ref: "components/schemas.md#/UUID" }
        required: [value_km, origin]
```

**Invariante "hodômetro nunca decresce"** (`shared/INVARIANTS.md`, reforçada por trigger/validação
de aplicação no Modelo Relacional — não é um `CHECK` de linha, precisa comparar contra a última
leitura do mesmo veículo): a API rejeita explicitamente uma leitura menor que a última registrada
para o mesmo `veiculo_tracionador_id`.

**Responses**

| Código | Corpo |
|---|---|
| `201` | `OdometerReading` |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — Veículo não existe |
| `422` | `UnprocessableEntity` — `FLEET_ODOMETER_READING_LOWER_THAN_LAST` (a invariante acima) |
| `500` | `InternalServerError` |

## Como este documento cresce

Nenhuma mudança prevista — o padrão D191/D246 é estável por definição (é o mesmo motivo de existir
para toda Time Series do sistema).
