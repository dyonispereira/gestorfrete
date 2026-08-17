# 022 — Implements

Bounded context proprietário: `fleet` (D215). Entidade independente — nunca um detalhe de
Composição Veicular (D076, já reconciliado no Modelo Relacional: `Implemento` tem identidade,
documentação e ciclo de vida próprios; `Composição Veicular` só referencia quais Implementos estão
combinados com qual Veículo Tracionador, quando).

## `GET /api/v1/implementos`

**Segurança**: `bearerAuth` + `fleet.implement.view`.

**Query parameters**: `page`/`limit`, `search` (`placa`/`codigo`), `tipo_carroceria`, `status`
(`status_disponibilidade`).

**Responses**: `200` (`Pagination` de `Implement`, `fleet-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/implementos/{id}`

**Segurança**: `fleet.implement.view`. **Responses**: `200`, `401`, `403`, `404`
(`FLEET_IMPLEMENT_NOT_FOUND`), `500`.

## `POST /api/v1/implementos`

**Segurança**: `fleet.implement.create`.

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
          body_type: { type: string, enum: [CARRETA, TANQUE, BAU, GRANELEIRO, PRANCHA, FRIGORIFICO, GAIOLA] }
          category_id: { $ref: "components/schemas.md#/UUID" }
          load_capacity: { type: string }
        required: [plate, renavam, body_type, category_id, load_capacity]
```

**Responses**: `201` (`Implement`), `400`, `401`, `403`, `409` (D230 — placa/código duplicados),
`500`.

## `PATCH /api/v1/implementos/{id}`

**Segurança**: `fleet.implement.edit`. D229 — parcial. `availability_status` **também** pode ser
alterado aqui (a exemplo de `Delivery` no Lote 4) — o ciclo `DISPONIVEL`/`EM_USO`/`INATIVO` de
Implemento não tem a complexidade de máquina de estados que justificaria um comando dedicado.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## `DELETE /api/v1/implementos/{id}`

**D219 — soft delete.** **Segurança**: `fleet.implement.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `FLEET_IMPLEMENT_IN_COMPOSITION` (Implemento
parte de uma Composição Veicular vigente — remover exigiria fechar a composição primeiro,
`023-vehicle-compositions.md`), `500`.

## Como este documento cresce

Nenhuma mudança prevista — `Implemento` é o cadastro mais simples deste lote.
