# 070 — Scheduled Updates (Agendamentos de Atualização)

Bounded context proprietário: `reporting` (D215). `agendamentos_atualizacao` — Master Data, D159:
**nunca executa cálculo** — só define a política consultada por `Execução de Job`
(`relational/010-administracao.md`), fora do escopo deste documento.

## Cron/periodicidade → solicita atualização, nunca calcula

```
Agendamento (modo: DIARIO)
        ↓
Execução de Job (010-administracao.md, fora deste lote) lê a política
        ↓
Dispara o recálculo real em analytics (062/063), fora deste endpoint
```

Este documento só expõe o **agendamento** (o quê + quando) — a execução em si (o cálculo de fato)
não é um endpoint aqui, é responsabilidade interna de `analytics`/`Execução de Job`.

## `GET /api/v1/reporting/scheduled-updates`

**Segurança**: `bearerAuth` + `reporting.scheduled_update.view`.

**Query parameters**: `page`/`limit`, `metric_id`, `cube_id`, `mode`, `status`.

**Responses**: `200` (`Pagination` de `ScheduledUpdate`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/reporting/scheduled-updates/{id}`

**Responses**: `200` (`ScheduledUpdate`), `401`, `403`, `404`, `500`.

## `POST /api/v1/reporting/scheduled-updates`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          metric_id: { $ref: "components/schemas.md#/UUID" }
          cube_id: { $ref: "components/schemas.md#/UUID" }
          mode: { type: string, enum: [TEMPO_REAL, INCREMENTAL, DIARIO, MANUAL] }
        required: [mode]
```

Exatamente um de `metric_id`/`cube_id` (`ck_agendamentos_atualizacao_alvo`) — `400` caso contrário.

**Segurança**: `reporting.scheduled_update.create`.

**Responses**: `201` (`ScheduledUpdate`), `400`, `401`, `403`, `404` (Métrica/Cubo não existe),
`500`.

## `PATCH /api/v1/reporting/scheduled-updates/{id}`

D229 — parcial (`mode`, `status`). Alvo (`metric_id`/`cube_id`) não é editável — trocar o alvo de
um agendamento é criar um novo, não editar o existente (o alvo é a identidade conceitual do
Agendamento).

**Segurança**: `reporting.scheduled_update.edit`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `reporting.scheduled_update.delete` — desativação via `PATCH
status=INATIVO`.

## Como este documento cresce

Se o produto pedir um cron expression explícito (hoje só `mode` categórico), isso é decisão de
Domain/DDL primeiro — `agendamentos_atualizacao` hoje não tem coluna de expressão cron, `modo` já
cobre os casos reais (`TEMPO_REAL`/`INCREMENTAL`/`DIARIO`/`MANUAL`).
