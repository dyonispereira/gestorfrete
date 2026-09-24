# 091 — Vehicle Categories

Bounded context proprietário: `fleet`. **D363 fechado (V1 Operational Hardening, Parte 5)** —
`VehicleCategory` (Aggregate Root, Entidade de Referência, D036) já existia no domínio desde o
Lote de Frota, sem `application`/`interfaces` próprias. Este documento formaliza o contrato HTTP
que faltava — nenhuma entidade nova, nenhum campo novo além dos já documentados em
`docs/domain/003-frota.md` ("Categoria de Veículo") e `docs/database/dictionary/003-frota.md`.

## Por que isso importava (Go-Live Audit)

`categoria_id` é FK obrigatória em Veículo Tracionador e Implemento — sem este contrato, a única
forma de cadastrar a estrutura mínima de frota era inserir a linha direto no banco. Fechar este
gap é o que permite a um Administrador cadastrar Veículo/Implemento sem SQL.

## `GET /api/v1/categorias-veiculo`

Lista paginada.

**Segurança**: `bearerAuth` + `fleet.vehicle_category.view`.

**Query parameters**: `page`, `limit`, `status` (`ATIVA`/`INATIVA`), `search` (contains, por `nome`).

**Responses**: `200` (`Pagination` de `VehicleCategory`), `401`, `403`, `500`.

## `GET /api/v1/categorias-veiculo/{id}`

**Segurança**: `fleet.vehicle_category.view`.

**Responses**: `200` (`VehicleCategory`), `401`, `403`, `404` — `FLEET_VEHICLE_CATEGORY_NOT_FOUND`, `500`.

## `POST /api/v1/categorias-veiculo`

**Segurança**: `fleet.vehicle_category.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
        required: [nome]
```

`codigo` é gerado internamente (mesmo padrão de `CostCenter.codigo`) — nunca informado pelo
cliente, não é um atributo documentado no Data Dictionary (só `nome`/`status` são).

**Responses**: `201` (`VehicleCategory`), `400`, `401`, `403`, `409` —
`FLEET_VEHICLE_CATEGORY_NAME_ALREADY_EXISTS` (`nome` único por tenant, invariante de domínio já
documentada), `500`.

## `PATCH /api/v1/categorias-veiculo/{id}`

**Segurança**: `fleet.vehicle_category.edit`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
          status: { type: string, enum: [ATIVA, INATIVA] }
```

`status: INATIVA` é a única forma de "desativar" uma Categoria — sem `DELETE`
(`RBAC_MATRIX.md` não tem `fleet.vehicle_category.delete`, mesmo padrão de `013-cost-centers.md`).

**Responses**: `200` (`VehicleCategory`), `400`, `401`, `403`, `404`, `409` (nome duplicado), `500`.

## `VehicleCategory` (schema)

```yaml
VehicleCategory:
  type: object
  properties:
    id: { $ref: "components/schemas.md#/UUID" }
    codigo: { type: string, readOnly: true }
    nome: { type: string }
    status: { type: string, enum: [ATIVA, INATIVA] }
    created_at: { type: string, format: date-time, readOnly: true }
    updated_at: { type: string, format: date-time, readOnly: true }
  required: [id, codigo, nome, status, created_at, updated_at]
```

## Como este documento cresce

Nenhuma mudança prevista — Categoria de Veículo é um cadastro de referência relativamente
estático (D036), sem evoluções futuras documentadas em `003-frota.md`.
