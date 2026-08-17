# 036 — Bank Accounts (Contas Bancárias)

Bounded context proprietário: `financial` (D215, D261). `contas_bancarias` — D189 (gap retroativo já
corrigido na Sprint 09, Modelo Relacional).

## D271 — RBAC não existia, corrigido na origem

Mesma auditoria de `034-chart-of-accounts.md`: `RBAC_MATRIX.md` §7.18 não tinha nenhum código para
Conta Bancária. Corrigido: `financial.bank_account.view`/`.create`/`.edit`/`.delete` adicionados
antes de escrever este documento (D271).

## `GET /api/v1/contas-bancarias`

**Segurança**: `bearerAuth` + `financial.bank_account.view`.

**Query parameters**: `page`/`limit`, `status`, `type` (`tipo`).

**Responses**: `200` (`Pagination` de `BankAccount`, `financial-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/contas-bancarias/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/contas-bancarias`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          bank: { type: string }
          branch: { type: string }
          account_number: { type: string }
          type: { type: string, enum: [CORRENTE, POUPANCA] }
        required: [bank, branch, account_number, type]
```

**Segurança**: `financial.bank_account.create`.

**Responses**: `201` (`BankAccount`), `400`, `401`, `403`, `409` — `numero_conta` duplicado
(`uq_contas_bancarias_tenant_id_numero`), `500`.

## `PATCH /api/v1/contas-bancarias/{id}`

D229 — parcial (`bank`, `branch`, `status`). `account_number`/`type` não editáveis após criação
(Atributo Crítico, D077-style — trocar dados bancários é evento raro e sensível, deve ser uma nova
conta, não uma edição silenciosa da existente).

**Segurança**: `financial.bank_account.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`,
`409`, `500`.

## `DELETE /api/v1/contas-bancarias/{id}`

**D219 — soft delete.**

**Segurança**: `financial.bank_account.delete`. **Responses**: `204`, `401`, `403`, `404`, `422` —
`FINANCIAL_BANK_ACCOUNT_IN_USE` (referenciada por `lancamentos_extrato_bancario` não conciliados),
`500`.

## `GET /api/v1/contas-bancarias/{id}/extrato`

Lançamentos do extrato bancário importado (`lancamentos_extrato_bancario`) — cursor-paginado
(Categoria Física Transactional de alto volume potencial, mesmo critério de `PAGINATION.md`).

**Segurança**: `financial.bank_reconciliation.view` (ver extrato é o primeiro passo da
conciliação — reaproveitado, sem código próprio de "ver extrato").

**Query parameters**: `cursor`, `limit`, `status` (`NAO_CONCILIADO`/`CONCILIADO`),
`date__gte`/`__lte` (`data`).

**Responses**: `200` (coleção cursor-paginada de `BankStatementEntry`, `financial-schemas.md`),
`401`, `403`, `404`, `500`.

## `GET /api/v1/contas-bancarias/{id}/saldo`

**D263 — saldo é sempre derivado.** Não existe um valor "saldo" digitável em nenhum lugar do
contrato — este endpoint calcula a partir de `contas_pagar`/`contas_receber` pendentes/pagas contra
esta conta, mesma fonte de `posicoes_caixa` (Read Model, `relational/006-financeiro.md`).

**Segurança**: `financial.bank_account.view`.

**Responses**

```yaml
"200":
  description: Saldo calculado
  content:
    application/json:
      schema:
        type: object
        properties:
          bank_account_id: { $ref: "components/schemas.md#/UUID" }
          balance: { $ref: "components/schemas.md#/Money" }
          calculated_at: { $ref: "components/schemas.md#/Timestamp" }
        required: [bank_account_id, balance, calculated_at]
```

`401`, `403`, `404`, `500`.

## `GET /api/v1/posicoes-caixa`

**Read Model puro** (`posicoes_caixa`, D081) — projeção diária de saldo projetado, nunca fonte de
verdade (mesmo princípio de `025-vehicle-availability.md`/D247, aplicado aqui ao caixa). **Sem
`POST`/`PATCH`/`DELETE`** — só processo automático escreve (`criado_por` nem existe na tabela).

**Segurança**: `financial.cash_flow.view`. **Query parameters**: `date__gte`/`__lte`
(`data_referencia`).

**Responses**: `200` (`Pagination` de objeto `{ data_referencia, saldo_projetado,
atualizado_em }`), `401`, `403`, `500`.

Não confundir com Fluxo de Caixa/DRE consolidado (`financial.cash_flow.view`/`.export`,
`financial.dre.view`/`.export`) — indicadores estatísticos completos vivem em `analytics`
(`011-bi.md`), fora deste lote (D090).

## Como este documento cresce

Se Open Finance for integrado (`005-FINANCEIRO.md`, "Requisitos futuros"), `POST /contas-bancarias/
{id}/extrato/importar` é candidato natural — hoje a importação de extrato não é detalhada (mecanismo
de `lancamentos_extrato_bancario` sendo populado fica para `037-bank-reconciliation.md` ou para o
lote de Integração).
