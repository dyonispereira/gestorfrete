# 057 — Driver Occurrences (Ocorrências do Motorista)

Bounded context proprietário: `freight` (D215) — não `mobile`. Superfície mobile-facing de
`017-trip-occurrences.md` — mesma entidade `Occurrence`, mesmo RBAC, D303 (nunca uma segunda
implementação).

## `GET /api/v1/mobile/trips/{id}/occurrences`

**Segurança**: `bearerAuth` + `freight.trip.view_own` (ver a viagem) + `freight.occurrence.view`.

**Responses**: `200` (`Pagination` de `Occurrence`, reaproveitado de `components/trip-schemas.md`),
`401`, `403`, `500`.

## `POST /api/v1/mobile/trips/{id}/occurrences`

Campos idênticos a `017-trip-occurrences.md` — tipo, descrição, localização, data/hora, evidências:

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          type: { type: string }
          description: { type: string }
          severity: { type: string, enum: [BAIXA, MEDIA, ALTA, CRITICA] }
          location:
            type: object
            properties:
              latitude: { type: number, format: double }
              longitude: { type: number, format: double }
            description: "Aceito no request, sem coluna física em `ocorrencias` (D242, gap já registrado em `017-trip-occurrences.md`) — mesma honestidade mantida aqui, não silenciosamente persistido."
          evidence_file_ids:
            type: array
            items: { $ref: "components/schemas.md#/UUID" }
            description: "D301 — fotos sempre por `arquivo_id`, nunca binário embutido."
        required: [type, description]
```

**Segurança**: `freight.occurrence.create` (App ●).

**Idempotency-Key**: obrigatório quando originado da Fila de Sincronização (`060-driver-sync.md`) —
o `identificador_local_unico` do item da fila já cumpre esse papel; quando chamado diretamente
(online), o cabeçalho `Idempotency-Key` é obrigatório do mesmo jeito (D211).

**Responses**: `201` (`Occurrence`), `400`, `401`, `403`, `404` (Viagem não existe ou não pertence
ao Motorista), `500`.

## Sem `PATCH`

`freight.occurrence.edit` existe mas **não** está marcado `●` (App) — edição de Ocorrência é
responsabilidade do Gestor Operacional (`017-trip-occurrences.md`), não do Motorista. Confirmado
por leitura da matriz, não assumido.

## Como este documento cresce

Nenhuma mudança estrutural prevista — segue `017-trip-occurrences.md` integralmente; qualquer
evolução do schema de `Occurrence` (ex: `location` ganhar coluna física) já propaga automaticamente
por reaproveitar o mesmo schema (D303).
