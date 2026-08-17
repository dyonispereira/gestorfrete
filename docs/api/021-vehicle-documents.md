# 021 — Vehicle Documents

Bounded context proprietário: `fleet` (D215). `documentos_veiculo` — sub-recurso de Veículo
(D232), `tipo` extensível (D120-style, ex.: CRLV) mas sempre validado contra o vocabulário já
declarado, nunca um campo livre que aceita qualquer string como "documento oficial" (leitura
literal do pedido: "não criar uma API genérica que permita anexar qualquer coisa como documento
oficial sem validação").

```
GET   /api/v1/veiculos/{id}/documentos
POST  /api/v1/veiculos/{id}/documentos
PATCH /api/v1/veiculos/{id}/documentos/{documentoId}
```

**Sem `DELETE`** — `RBAC_MATRIX.md` 7.8 só tem `fleet.vehicle_document.view`/`.create`/`.attach`,
sem código de exclusão (confirmado por leitura completa da seção, não assumido). Um documento
vencido não é removido, só permanece com `status: VENCIDO` até ser substituído por um novo
registro — histórico de documentação é auditável.

## `GET /api/v1/veiculos/{id}/documentos`

**Segurança**: `bearerAuth` + `fleet.vehicle_document.view`.

**Query parameters**: `page`/`limit`, `type`, `status`.

**Responses**: `200` (`Pagination` de `VehicleDocument`, `fleet-schemas.md`), `401`, `403`, `404`,
`500`.

## `POST /api/v1/veiculos/{id}/documentos`

**Segurança**: `fleet.vehicle_document.attach` (não `.create` isoladamente — na prática, criar um
Documento de Veículo sempre envolve anexar um arquivo, D251; `.attach` é a permissão que já cobre
o caso completo, `.create` fica reservado para o cenário raro de registrar metadados sem arquivo
ainda, mesma permissão usada nos dois casos por não haver diferenciação de rota).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          type: { type: string, example: "CRLV" }
          number: { type: string }
          expires_at: { type: string, format: date }
          file_id:
            $ref: "components/schemas.md#/UUID"
            description: "D251 — referência ao Storage. O upload do arquivo em si acontece por um
              fluxo separado (fora deste lote), que devolve este `file_id` para ser referenciado
              aqui — nunca o binário dentro deste corpo JSON."
        required: [type, number, expires_at]
```

**Responses**: `201` (`VehicleDocument`), `400`, `401`, `403`, `404`, `500`.

## `PATCH /api/v1/veiculos/{id}/documentos/{documentoId}`

**Segurança**: `fleet.vehicle_document.attach` — mesma nota acima; **não existe
`fleet.vehicle_document.edit`** em `RBAC_MATRIX.md` (confirmado, não assumido), então esta é a
permissão reaproveitada para atualizar metadados/substituir o arquivo (D240-style: lacuna de
granularidade documentada, não uma permissão nova inventada).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          number: { type: string }
          expires_at: { type: string, format: date }
          file_id: { $ref: "components/schemas.md#/UUID" }
```

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## Como este documento cresce

Se o produto precisar de exclusão de Documento de Veículo, a Permissão nasce primeiro em
`RBAC_MATRIX.md` (registrada como decisão), só então o endpoint — mesma disciplina de
`013-cost-centers.md`.
