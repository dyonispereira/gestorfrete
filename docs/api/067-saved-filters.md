# 067 — Saved Filters (Filtros Favoritos)

Bounded context proprietário: `reporting` (D215). `filtros_favoritos` — Master Data, sempre do
próprio usuário.

## Nunca "filtros globais" do sistema

Pedido explícito: um Filtro Favorito é sempre pessoal (`usuario_id NOT NULL`) — não existe conceito
de filtro compartilhado/global neste lote (diferente de Dashboard, que tem `sharing`). Promover um
filtro a "global" exigiria uma entidade nova, fora de escopo (D076 — não inventado aqui).

## `GET /api/v1/reporting/saved-filters`

**Segurança**: `bearerAuth` + `reporting.saved_filter.view_own`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `status`.

**Responses**: `200` (`Pagination` de `SavedFilter`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/reporting/saved-filters/{id}`

**Segurança**: `reporting.saved_filter.view_own` — `403` se não pertence ao usuário.

**Responses**: `200` (`SavedFilter`), `401`, `403`, `500`.

## `POST /api/v1/reporting/saved-filters`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          criteria: { type: object }
        required: [name, criteria]
```

**Segurança**: `reporting.saved_filter.create`.

**Responses**: `201` (`SavedFilter`), `400`, `401`, `403`, `409` (`name` duplicado por usuário),
`500`.

## `PATCH /api/v1/reporting/saved-filters/{id}`

D229 — parcial (`name`, `criteria`, `status`).

**Segurança**: `reporting.saved_filter.edit_own`. **Responses**: `200`, `400`, `401`, `403`, `404`,
`409`, `500`.

## `DELETE /api/v1/reporting/saved-filters/{id}`

**D219 — soft delete.** **Segurança**: `reporting.saved_filter.delete_own`.

**Responses**: `204`, `401`, `403`, `404`, `500`.

## Como este documento cresce

Se compartilhamento de Filtro for pedido no futuro, segue o mesmo padrão já estabelecido em
Dashboard (`066`) — campo `sharing` + comando `commands/share` — não inventado por antecipação
aqui.
