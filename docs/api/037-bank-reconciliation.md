# 037 — Bank Reconciliation (Conciliação Bancária) e Estorno Financeiro

Bounded context proprietário: `financial` (D215, D261). Fluxo pedido explicitamente: Extrato →
Lançamento bancário → Possível correspondência → Conciliação.

## Extrato → Lançamento → Correspondência → Conciliação

- **Extrato**: arquivo/feed importado (fora de escopo eletrônico desta fundação, `005-
  FINANCEIRO.md`) — resulta em linhas de `BankStatementEntry` (`lancamentos_extrato_bancario`),
  expostas via `GET /contas-bancarias/{id}/extrato` (`036-bank-accounts.md`).
- **Lançamento bancário** = `BankStatementEntry` — já é a entidade física, não recriada aqui.
- **Possível correspondência**: cálculo de candidatos (valor + data aproximada contra Contas a
  Pagar/Receber pendentes) — **não modelado como endpoint de sugestão** neste lote (não existe
  tabela/RBAC para "sugestões de conciliação"; a correspondência é decidida pelo usuário no momento
  de `POST /conciliacoes-bancarias`, ver abaixo — nenhuma entidade nova inventada, D076).
- **Conciliação** = `BankReconciliation` (`conciliacoes_bancarias`), a única escrita real deste
  fluxo.

## `GET /api/v1/conciliacoes-bancarias`

**Segurança**: `bearerAuth` + `financial.bank_reconciliation.view`.

**Query parameters**: `page`/`limit`, `bank_account_id` (via `bank_statement_entry_id`, indireto —
ver nota), `divergence` (`divergencia`), `accounts_payable_id` (`conta_pagar_id`),
`accounts_receivable_id` (`conta_receber_id`).

**Responses**: `200` (`Pagination` de `BankReconciliation`, `financial-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/conciliacoes-bancarias/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/conciliacoes-bancarias`

Registra a correspondência entre um Lançamento de Extrato e uma Conta a Pagar/Receber — é este
`POST` que, como efeito colateral, transiciona `PAGA → CONCILIADA` (`032`) ou `RECEBIDA →
CONCILIADA` (`033`).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          bank_statement_entry_id: { $ref: "components/schemas.md#/UUID" }
          accounts_payable_id: { $ref: "components/schemas.md#/UUID" }
          accounts_receivable_id: { $ref: "components/schemas.md#/UUID" }
          divergence: { type: boolean, default: false }
        required: [bank_statement_entry_id]
```

Exatamente um de `accounts_payable_id`/`accounts_receivable_id` (`ck_conciliacoes_bancarias_alvo_
exclusivo`) — `400` caso contrário. `bank_statement_entry_id` só pode ser usado uma vez
(`uq_conciliacoes_bancarias_lancamento_extrato_id`) — `409` em segunda tentativa.

**Segurança**: `financial.bank_reconciliation.create`. **Idempotency-Key**: obrigatório (D211 —
conciliação é uma das operações críticas listadas).

**Responses**: `201` (`BankReconciliation`), `400`, `401`, `403`, `404` (Lançamento/Conta a Pagar/
Conta a Receber não existe), `409` — `FINANCIAL_RECONCILIATION_ENTRY_ALREADY_USED` /
`FINANCIAL_PAYABLE_INVALID_TRANSITION` / `FINANCIAL_RECEIVABLE_INVALID_TRANSITION` (a conta alvo
não está em `PAGA`/`RECEBIDA`), `500`.

## `divergence = true` — divergência de conciliação

Quando o valor do Lançamento diverge do valor da Conta a Pagar/Receber (desconto não combinado,
taxa de gateway), o cliente envia `divergence: true` — **gera Ocorrência financeira para
investigação manual** (`005-FINANCEIRO.md`) — mesmo texto de `033`, sem endpoint de Ocorrência
Financeira detalhado neste lote (fora de escopo, mesmo padrão em ambos os documentos).

## Sem `PATCH`/`DELETE`

Conciliação é um registro pontual — corrigir uma conciliação errada é via `FinancialReversal`
(abaixo), nunca editando/removendo o registro de conciliação (mesmo princípio de D037 aplicado a
todo histórico do sistema).

## `FinancialReversal` — Estorno Financeiro

D266 — mecanismo único de correção pós-fato para Fatura/Conta a Pagar/Conta a Receber. D270 —
`EstornoRealizado` adicionado a `EVENT_MAP.md` nesta preparação (gap encontrado, corrigido antes de
escrever este documento).

### `GET /api/v1/estornos-financeiros`

**Segurança**: `financial.reversal.view` — código adicionado nesta preparação (D271, junto com
`chart_of_accounts`/`bank_account`).

**Query parameters**: `page`/`limit`, `invoice_id`, `accounts_payable_id`, `accounts_receivable_id`.

**Responses**: `200` (`Pagination` de `FinancialReversal`), `401`, `403`, `500`.

### `GET /api/v1/estornos-financeiros/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### `POST /api/v1/estornos-financeiros`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          invoice_id: { $ref: "components/schemas.md#/UUID" }
          accounts_payable_id: { $ref: "components/schemas.md#/UUID" }
          accounts_receivable_id: { $ref: "components/schemas.md#/UUID" }
          value: { type: string }
          reason: { type: string }
        required: [value, reason]
```

Exatamente um dos três alvos (`ck_estornos_financeiros_alvo_exclusivo`) — `400` caso contrário. Não
altera `status`/`valor` do registro original (D266 — preserva histórico); só cria o registro de
correção, referenciado junto ao original em qualquer consulta.

**Segurança**: `financial.reversal.create`. **Idempotency-Key**: obrigatório (D211).

**Responses**: `201` (`FinancialReversal`), `400`, `401`, `403`, `404` (alvo não existe), `500`.

### Sem `PATCH`/`DELETE`

Estorno é, ele mesmo, o mecanismo de correção — corrigir um Estorno errado exigiria um novo Estorno
apontando para o mesmo alvo, não editar/remover o registro existente (mesmo princípio recursivo já
aplicado a toda entidade Histórica do sistema, D037).

## Fora de escopo, não esquecido

- **Cálculo de candidatos de correspondência** (sugestão automática extrato↔conta): não modelado —
  sem tabela/RBAC, `POST /conciliacoes-bancarias` já exige que o cliente informe o alvo.
- **Ocorrência financeira**: mesma lacuna de `033-accounts-receivable.md`.
- **Importação eletrônica de extrato** (Open Finance): `005-FINANCEIRO.md`, "Requisitos futuros".

## Como este documento cresce

Se sugestão automática de correspondência for pedida no futuro, um `GET /contas-bancarias/{id}/
extrato/{entryId}/candidatos` é o candidato natural de endpoint — hoje deliberadamente não
construído para não inventar uma capacidade de matching que o domínio não especificou.
