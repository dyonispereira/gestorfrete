# 062 — Metrics (Métricas)

Bounded context proprietário: `analytics` (D215). `metricas` — Reference Data (D036), Aggregate
Root. D306: catálogo puro, nunca altera dado operacional.

## D313 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.23 só tinha códigos de relatórios pré-construídos, nenhum para o sistema
flexível de Métrica/Indicador/Snapshot/Cubo. Corrigido: `analytics.metric.view`/`.create`/`.edit`
adicionados antes de escrever este documento.

## `GET /api/v1/analytics/metrics`

**Segurança**: `bearerAuth` + `analytics.metric.view`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `temporal_granularity`,
`dimensional_granularity`, `status`.

**Responses**: `200` (`Pagination` de `Metric`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/analytics/metrics/{id}`

**Responses**: `200` (`Metric`), `401`, `403`, `404`, `500`.

## `POST /api/v1/analytics/metrics`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          formula: { type: string }
          temporal_granularity: { type: string, enum: [DIARIO, SEMANAL, MENSAL, POR_EVENTO] }
          dimensional_granularity: { type: string, enum: [VIAGEM, VEICULO, MOTORISTA, CLIENTE, TENANT] }
          unit: { type: string }
          data_sources: { type: object }
          calculation_periodicity: { type: string, enum: [TEMPO_REAL, INCREMENTAL, DIARIO, MANUAL] }
        required: [name, formula, temporal_granularity, dimensional_granularity, unit, calculation_periodicity]
```

`version` nasce sempre `1` — nunca aceito no corpo. **Segurança**: `analytics.metric.create`.

**Responses**: `201` (`Metric`), `400`, `401`, `403`, `409` (`nome` duplicado no tenant/plataforma),
`500`.

## `PATCH /api/v1/analytics/metrics/{id}` — D155, nunca sobrescreve a fórmula histórica

Alterar `formula` **cria uma nova versão** (`version` incrementado), nunca um `UPDATE` na linha
lógica anterior — `Indicador Consolidado` (`063`) já calculado continua referenciando a
`metric_version` antiga (`metrica_versao`, cópia fixa). Demais campos (`name`/`unit`/
`data_sources`/`calculation_periodicity`/`status`) podem ser editados sem gerar nova versão.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          formula: { type: string, description: "Alterar este campo incrementa `version` automaticamente." }
          unit: { type: string }
          data_sources: { type: object }
          calculation_periodicity: { type: string, enum: [TEMPO_REAL, INCREMENTAL, DIARIO, MANUAL] }
          status: { type: string, enum: [ATIVA, DESCONTINUADA] }
```

**Segurança**: `analytics.metric.edit`.

**Responses**: `200` (`Metric`, `version` refletindo o incremento se `formula` mudou), `400`, `401`,
`403`, `404`, `500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `analytics.metric.delete` — descontinuação via `PATCH
status=DESCONTINUADA`, mesmo padrão de toda Reference Data com campo de status neste sistema.
Métrica nunca é excluída fisicamente: `Indicador Consolidado`/`Snapshot Analítico` históricos
sempre precisam conseguir referenciar a Métrica que os gerou (D156).

## Como este documento cresce

Nenhuma mudança estrutural prevista — o padrão de versionamento (D155) é estável por definição.
