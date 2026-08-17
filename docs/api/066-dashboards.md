# 066 — Dashboards

Bounded context proprietário: `reporting` (D215). `dashboards_personalizados` — Master Data,
D152: **nunca guarda valor de KPI**, só configuração/referência.

## `GET /api/v1/reporting/dashboards`

Lista os dashboards do próprio usuário **e** os compartilhados com ele.

**Segurança**: `bearerAuth` + `reporting.dashboard.view_own` (próprios) +
`reporting.dashboard.view_shared` (compartilhados) — a resposta combina os dois conjuntos conforme
as permissões que o chamador tiver.

**Query parameters**: `page`/`limit`, `search` (`nome`), `status`.

**Responses**: `200` (`Pagination` de `Dashboard`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/reporting/dashboards/{id}`

**Segurança**: `.view_own` (dono) ou `.view_shared` (`permissoes_compartilhamento` inclui o
usuário) — `403` caso contrário.

**Responses**: `200` (`Dashboard`), `401`, `403`, `404`, `500`.

## `POST /api/v1/reporting/dashboards`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          layout: { type: object }
          widgets:
            type: array
            items:
              type: object
              properties:
                metric_id: { $ref: "components/schemas.md#/UUID" }
                indicator_id: { $ref: "components/schemas.md#/UUID" }
                visualization_type: { type: string }
          filters: { type: object }
          preferences: { type: object }
        required: [name, layout, widgets]
```

Cada widget referencia `metric_id` **ou** `indicator_id` (D158, cada widget pode vir de origem
diferente) — nunca copia valor, sempre referência.

**Segurança**: `reporting.dashboard.create`.

**Responses**: `201` (`Dashboard`), `400`, `401`, `403`, `404` (Métrica/Indicador referenciado não
existe), `409` (`name` duplicado por usuário), `500`.

## `PATCH /api/v1/reporting/dashboards/{id}`

D229 — parcial. **Segurança**: `reporting.dashboard.edit_own` — só o dono edita (compartilhamento
nunca inclui edição, só visualização).

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## `DELETE /api/v1/reporting/dashboards/{id}`

**D219 — soft delete.** **Segurança**: `reporting.dashboard.delete_own`.

**Responses**: `204`, `401`, `403`, `404`, `500`.

## `POST /api/v1/reporting/dashboards/{id}/commands/share`

Comando explícito para alterar `sharing` (`permissoes_compartilhamento`) — separado de `PATCH`
porque compartilhar é uma responsabilidade RBAC-sensível própria (D234-style, intenção explícita).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          sharing: { type: string, enum: [PRIVADO, COMPARTILHADO_COM_GRUPO, COMPARTILHADO_COM_PAPEL] }
        required: [sharing]
```

**Segurança**: `reporting.dashboard.share`.

**Responses**: `200` (`Dashboard`), `400`, `401`, `403`, `404`, `500`.

## Como este documento cresce

Se o produto pedir compartilhamento granular (usuário específico, não só grupo/papel), isso exige
primeiro uma mudança de Domain/DDL (`permissoes_compartilhamento` hoje é um Enum fechado) — nunca
simulado neste contrato sem a coluna física correspondente.
