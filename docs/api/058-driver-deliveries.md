# 058 — Driver Deliveries (Entregas do Motorista)

Bounded context proprietário: `freight` (D215) — não `mobile`. Superfície mobile-facing de
`015-trip-deliveries.md` — mesma entidade `Delivery`/`ProofOfDelivery`, mesmo RBAC, D303.

## `GET /api/v1/mobile/trips/{id}/deliveries`

**Segurança**: `bearerAuth` + `freight.trip.view_own` + `freight.delivery.view`.

**Responses**: `200` (`Pagination` de `Delivery`, reaproveitado de `components/trip-schemas.md`),
`401`, `403`, `500`.

## `GET /api/v1/mobile/trips/{id}/deliveries/{deliveryId}`

**Responses**: `200` (`Delivery`), `401`, `403`, `404`, `500`.

## `POST /api/v1/mobile/trips/{id}/deliveries/{deliveryId}/pod`

**Canhoto** — mesmo comando de `015-trip-deliveries.md`, path mobile-facing. Cria o Canhoto **e**,
quando `signature_file_id` presente, a `DigitalSignature` correspondente (`document_type =
CANHOTO`) na mesma transação — coerente com o pedido do usuário ("caso pertença a uma ação de
entrega, preferir o comando da entrega") e com D303 (nunca uma segunda implementação para a mesma
operação).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          photo_file_id: { $ref: "components/schemas.md#/UUID" }
          signature_file_id: { $ref: "components/schemas.md#/UUID" }
          signatory_role: { type: string, enum: [MOTORISTA, CLIENTE, RECEBEDOR] }
          signatory_name: { type: string, description: "Obrigatório quando `signatory_role = RECEBEDOR` sem cadastro." }
        required: [photo_file_id, signature_file_id, signatory_role]
```

**Segurança**: `freight.pod.create` + `freight.pod.attach` (ambos App ●). **Idempotency-Key**:
obrigatório (D211 — canhoto é operação crítica, nunca duplicável).

**Responses**: `201` (`ProofOfDelivery`), `400`, `401`, `403`, `404`, `409` —
`FREIGHT_DELIVERY_INVALID_STATUS` (Entrega já tem Canhoto ou não está no estado que aceita
confirmação — ver `015-trip-deliveries.md`), `500`.

## `commands/register` (Entrega)

Registrar uma entrega (`freight.delivery.create`, App ●) — mesmo comando de `015`, path mobile.
Ver `015-trip-deliveries.md` para o corpo completo (endereço/janela/status inicial) — não repetido
aqui para não duplicar especificação (D303 aplicado também à documentação, não só ao código).

**Responses**: idênticas a `015-trip-deliveries.md`.

## Sem `PATCH` de Entrega

`freight.delivery.edit` existe mas não está marcado `●` — edição de dados de Entrega (endereço,
janela) é responsabilidade do Gestor Operacional, não do Motorista em campo.

## Como este documento cresce

Segue `015-trip-deliveries.md` integralmente — qualquer novo campo/regra em Canhoto/Entrega já
propaga automaticamente por reaproveitar o mesmo schema.
