# 064 — Analytical Snapshots (Snapshots Analíticos)

Bounded context proprietário: `analytics` (D215). `snapshots_analiticos` — Histórica, **imutável
após `CONSOLIDADO`** (D151).

## `GET /api/v1/analytics/snapshots`

**Segurança**: `bearerAuth` + `analytics.snapshot.view`.

**Query parameters**: `page`/`limit`, `reference_period`, `processing_origin`
(`AUTOMATICO`/`MANUAL`), `status`.

**Responses**: `200` (`Pagination` de `AnalyticalSnapshot`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/analytics/snapshots/{id}`

**Responses**: `200` (`AnalyticalSnapshot`, incluindo `participating_metrics`/`indicator_ids` —
D160, rastreabilidade completa nunca um fechamento opaco), `401`, `403`, `404`, `500`.

## `POST /api/v1/analytics/snapshots`

**Só inicia a consolidação** — o domínio permite (pedido explícito confirmado contra
`snapshots_analiticos_origem_processamento_enum`, que tem `MANUAL` como valor real, não inventado).
Cria o registro em `EM_PROCESSAMENTO`; a consolidação em si (agregação dos Indicadores) é
assíncrona, mesmo espírito de `069-exports.md`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          reference_period: { type: string }
        required: [reference_period]
```

`origin` nasce sempre `MANUAL` quando disparado por este endpoint (o valor `AUTOMATICO` é reservado
para o consumidor de `Agendamento de Atualização`, `070`, nunca aceito no corpo aqui).

**Segurança**: `analytics.snapshot.create`. **Idempotency-Key**: obrigatório (D211 — consolidar o
mesmo período duas vezes não pode gerar dois snapshots concorrentes).

**Responses**: `201` (`AnalyticalSnapshot`, `status = EM_PROCESSAMENTO`), `400`, `401`, `403`,
`409` — `ANALYTICS_SNAPSHOT_PERIOD_ALREADY_CONSOLIDATED`, `500`.

## Sem `PATCH`/`DELETE` — resultado consolidado nunca editável

**D151, pedido explícito**: uma vez `CONSOLIDADO`, o Snapshot e todos os Indicadores que ele
absorveu (`status → SNAPSHOTADO`) são imutáveis. A única transição de status possível depois de
criado é interna (`EM_PROCESSAMENTO → CONSOLIDADO` ou `→ INVALIDO`, quando um erro grave nos dados
de origem é descoberto **antes** de fechar oficialmente) — nenhuma delas é um `PATCH` do cliente,
ambas resultam do processamento assíncrono disparado pelo `POST` acima.

## Como este documento cresce

Se o produto pedir um comando explícito de "invalidar snapshot" (hoje só descrito como resultado
interno do processamento), isso é aditivo — nunca reabre um snapshot já `CONSOLIDADO` para
`EM_PROCESSAMENTO` (D151 é absoluto).
