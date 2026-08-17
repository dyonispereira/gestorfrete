# 063 — Consolidated Indicators (Indicadores Consolidados)

Bounded context proprietário: `analytics` (D215). `indicadores_consolidados` — Transactional/
Histórica, calculada pela aplicação, nunca digitada.

## Métrica → Indicador → Snapshot

Cadeia de responsabilidade explícita: **Métrica** (`062`) define a fórmula e sua versão; um
**Indicador Consolidado** é o resultado de aplicar uma versão específica da fórmula a uma dimensão/
período; um **Snapshot Analítico** (`064`) congela um conjunto de Indicadores num fechamento
imutável. Nenhum nível pula o anterior — um Indicador sempre referencia `metric_id`+
`metric_version`, nunca contém a fórmula em si (D156).

## `GET /api/v1/analytics/indicators`

**Segurança**: `bearerAuth` + `analytics.indicator.view`.

**Query parameters**: `page`/`limit`, `metric_id`, `dimension_type`, `dimension_id`,
`reference_period`, `status`.

**Responses**: `200` (`Pagination` de `ConsolidatedIndicator`, `bi-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/analytics/indicators/{id}`

**Responses**: `200` (`ConsolidatedIndicator`), `401`, `403`, `404`, `500`.

## Sem `POST`/`PATCH`/`DELETE`

**Nunca aceita fórmula ou valor no request** (pedido explícito) — todo Indicador Consolidado nasce
do processamento interno de `analytics` (disparado por `Agendamento de Atualização`, `070`, ou por
consolidação de Snapshot, `064`), nunca de uma escrita direta do cliente HTTP. `RBAC_MATRIX.md`
confirma: só `.view` existe para `indicator`, nenhum verbo de escrita.

## Governança (D151) — refletida no `status`

| `status` | Significado |
|---|---|
| `VALIDO` | Nenhum recálculo/snapshot afetou ainda |
| `RECALCULADO` | Uma execução mais nova da mesma Métrica/período gerou um valor mais novo (o anterior não é apagado, D037 — consultável por período/data de cálculo) |
| `SNAPSHOTADO` | Entrou em um Snapshot Analítico `CONSOLIDADO` — imutável a partir daqui, nenhum processo recalcula (D151) |

## Como este documento cresce

Nenhuma mudança estrutural prevista — leitura pura, estável por definição enquanto o padrão
Métrica→Indicador→Snapshot não mudar.
