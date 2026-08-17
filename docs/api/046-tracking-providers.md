# 046 — Tracking Providers (Provedores de Rastreamento)

Bounded context proprietário: `tracking` (D215). Recurso administrativo — `provedores_rastreamento`.

## D291 — domínio agnóstico de fornecedor

**Nenhuma integração específica por fornecedor é criada aqui.** Este é só o cadastro (nome/status)
que `047-tracking-devices.md` referencia via `provider_id` — a lógica de comunicação com cada
provedor (protocolo, formato de payload) pertence à camada de Integração (fora do escopo desta API
pública, D278-style aplicado a `tracking`).

## D293 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.16 não tinha nenhum código para Provedor de Rastreamento antes desta preparação
(D200 aplicado à API) — quarta ocorrência desse tipo de lacuna nesta sprint (após `financial.
chart_of_accounts`/`.bank_account`, D271; `documents.fiscal_config`, D283). Corrigido:
`tracking.provider.view`/`.create`/`.edit` adicionados antes de escrever este documento.

## `GET /api/v1/tracking/providers`

**Segurança**: `bearerAuth` + `tracking.provider.view`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `status`.

**Responses**: `200` (`Pagination` de `TrackingProvider`, `tracking-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/tracking/providers/{id}`

**Responses**: `200` (`TrackingProvider`), `401`, `403`, `404`, `500`.

## `POST /api/v1/tracking/providers`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
        required: [name]
```

**Segurança**: `tracking.provider.create`.

**Responses**: `201` (`TrackingProvider`), `400`, `401`, `403`, `409` (`nome` duplicado no tenant),
`500`.

## `PATCH /api/v1/tracking/providers/{id}`

D229 — parcial (`name`, `status`).

**Segurança**: `tracking.provider.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409`,
`500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `tracking.provider.delete` — desativação via `PATCH status=INATIVO`,
mesmo padrão de `013-cost-centers.md`/`029-preventive-maintenance-plans.md`. Um provedor
`INATIVO` continua referenciado por `Equipamentos` já existentes (histórico nunca quebra por
desativação de cadastro, D001).

## Como este documento cresce

Se o produto precisar de metadados por provedor (ex: URL de webhook, formato de payload esperado),
isso é decisão de Domain/DDL primeiro (D101/D102) — `provedores_rastreamento` hoje só tem
`nome`/`status`, nada além disso é inventado aqui.
