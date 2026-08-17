# 065 — Analytics Cubes (Cubos Analíticos)

Bounded context proprietário: `analytics` (D215). `cubos_analiticos` — Reference Data (D036),
**só a definição estrutural** (dimensões/medidas) — pedido explícito: nenhuma implementação de
infraestrutura mencionada no contrato.

## Domínio-agnóstico de infraestrutura de execução

`cubos_analiticos`/`AnalyticsCube` nunca mencionam ClickHouse/BigQuery/Power BI/DuckDB ou qualquer
motor de OLAP — mesmo princípio de D170 (Modelo de IA nunca é o fornecedor) e D291 (Rastreamento
nunca expõe fornecedor), aplicado aqui à camada de infraestrutura analítica. A tabela física já
confirma isso: `relational/011-bi.md` é explícito — "apenas a definição estrutural... nenhuma
tabela de dados materializados do cubo nesta fundação".

## `GET /api/v1/analytics/cubes`

**Segurança**: `bearerAuth` + `analytics.cube.view`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `status`.

**Responses**: `200` (`Pagination` de `AnalyticsCube`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/analytics/cubes/{id}`

**Responses**: `200` (`AnalyticsCube`), `401`, `403`, `404`, `500`.

## `POST /api/v1/analytics/cubes`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          dimensions: { type: array, items: { type: string }, minItems: 1 }
          metric_ids: { type: array, items: { $ref: "components/schemas.md#/UUID" }, minItems: 1 }
        required: [name, dimensions, metric_ids]
```

**Segurança**: `analytics.cube.create`.

**Responses**: `201` (`AnalyticsCube`), `400`, `401`, `403`, `404` (Métrica não existe), `409`
(`nome` duplicado no tenant), `500`.

## `PATCH /api/v1/analytics/cubes/{id}`

D229 — parcial (`dimensions`, `metric_ids`, `status`).

**Segurança**: `analytics.cube.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409`,
`500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `analytics.cube.delete` — desativação via `PATCH status=INATIVO`.

## Como este documento cresce

Se o produto decidir materializar dados de cubo fisicamente no futuro, isso é uma tabela/decisão
nova em `relational/011-bi.md` primeiro (D101/D102) — este contrato continua descrevendo só a
definição estrutural, nunca o dado materializado.
