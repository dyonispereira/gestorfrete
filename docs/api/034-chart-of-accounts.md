# 034 — Chart of Accounts (Plano de Contas)

Bounded context proprietário: `financial` (D215, D261). Já absorve o conceito de "Categoria
Financeira" (`relational/006-financeiro.md`, D184) — nenhuma entidade separada foi criada.

## D271 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.18 não tinha nenhum código para Plano de Contas antes desta preparação (D200
aplicado à API) — nem mesmo coarse-grained, diferente de toda lacuna anterior desta sprint (que
sempre tinha ao menos um código na família a reaproveitar). Corrigido: `financial.chart_of_
accounts.view`/`.create`/`.edit`/`.delete` adicionados a `RBAC_MATRIX.md` antes de escrever este
documento — mesmo princípio de D222/D196 (fonte física plenamente especificada, artefato downstream
que nunca a materializou), aplicado desta vez à matriz de permissões em vez de à DDL.

## `GET /api/v1/plano-contas`

**Segurança**: `bearerAuth` + `financial.chart_of_accounts.view`.

**Query parameters**: `page`/`limit`, `search` (`nome`/`codigo_contabil`), `type` (`tipo`),
`parent_id` (`categoria_pai_id`), `status`.

**Responses**: `200` (`Pagination` de `ChartOfAccounts`, `financial-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/plano-contas/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/plano-contas`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          account_code: { type: string }
          name: { type: string }
          type: { type: string, enum: [RECEITA, DESPESA] }
          parent_id: { $ref: "components/schemas.md#/UUID" }
        required: [account_code, name, type]
```

**Segurança**: `financial.chart_of_accounts.create`.

**Responses**: `201` (`ChartOfAccounts`), `400`, `401`, `403`, `404` (`parent_id` não existe), `409`
— `codigo_contabil` duplicado (`uq_plano_contas_tenant_id_codigo`), `500`.

## `PATCH /api/v1/plano-contas/{id}`

D229 — parcial. Alterar `parent_id` valida ausência de ciclo (percorre `categoria_pai_id` até a
raiz, `relational/006-financeiro.md`) — `422` se a conta nova-pai for a própria conta ou uma
descendente dela.

**Segurança**: `financial.chart_of_accounts.edit`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `422` —
`FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED`, `500`.

## `DELETE /api/v1/plano-contas/{id}`

**D219 — soft delete**, com duas precondições explícitas pedidas no kickoff:

**Segurança**: `financial.chart_of_accounts.delete`.

**Responses**

| Código | Corpo |
|---|---|
| `204` | Excluída |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `409` | `FINANCIAL_CHART_OF_ACCOUNTS_HAS_ACTIVE_CHILDREN` — existe conta filha com `status = ATIVO` |
| `409` | `FINANCIAL_CHART_OF_ACCOUNTS_IN_USE` — referenciada por `contas_pagar.plano_contas_id` |
| `500` | `InternalServerError` |

## Como este documento cresce

Nenhuma mudança estrutural prevista — Plano de Contas é Reference Data hierárquica estável por
natureza (D036).
