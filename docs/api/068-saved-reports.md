# 068 — Saved Reports (Relatórios Salvos)

Bounded context proprietário: `reporting` (D215). `relatorios_salvos` — Master Data, sempre do
próprio usuário.

## Configuração, nunca query física

**Nunca duplica queries físicas do banco** (pedido explícito) — `Relatório Salvo` só guarda
`metric_ids`/`filters`/`output_format`: **o que** deve compor o relatório e **como** deve ser
exportado, nunca **como** a consulta é executada (isso é responsabilidade de `analytics` ao
resolver os `metric_ids` referenciados, detalhe de implementação de Backend, nunca exposto aqui).

## `GET /api/v1/reporting/saved-reports`

**Segurança**: `bearerAuth` + `reporting.saved_report.view_own`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `output_format`, `status`.

**Responses**: `200` (`Pagination` de `SavedReport`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/reporting/saved-reports/{id}`

**Segurança**: `reporting.saved_report.view_own`. **Responses**: `200` (`SavedReport`), `401`,
`403`, `404`, `500`.

## `POST /api/v1/reporting/saved-reports`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          metric_ids:
            type: array
            items: { $ref: "components/schemas.md#/UUID" }
            minItems: 1
          filters: { type: object }
          output_format: { type: string, enum: [PDF, EXCEL, CSV] }
        required: [name, metric_ids, output_format]
```

**Segurança**: `reporting.saved_report.create`.

**Responses**: `201` (`SavedReport`), `400`, `401`, `403`, `404` (Métrica referenciada não existe),
`409` (`name` duplicado por usuário), `500`.

## `PATCH /api/v1/reporting/saved-reports/{id}`

D229 — parcial. **Segurança**: `reporting.saved_report.edit_own`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## `DELETE /api/v1/reporting/saved-reports/{id}`

**D219 — soft delete.** **Segurança**: `reporting.saved_report.delete_own`. Excluir um Relatório
Salvo referenciado por uma `Export` (`069`) não apaga a exportação já gerada (D001, histórico
nunca quebra por desativação de cadastro — mesmo princípio de `046-tracking-providers.md`).

**Responses**: `204`, `401`, `403`, `404`, `500`.

## Como este documento cresce

Gerar uma exportação a partir de um Relatório Salvo é `069-exports.md`'s `POST /reporting/exports`
com `saved_report_id` preenchido — nunca um endpoint próprio de "exportar este relatório" aqui, D303
aplicado dentro do próprio módulo de BI (uma única forma de gerar exportação).
