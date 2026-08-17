# components/financial-schemas.md — Schemas de Financeiro

Bounded context `financial` (D215, D261) — exceto `SubscriptionPlan`/`Subscription`/
`RecurringCharge`, que pertencem a `subscription`/`billing` (D272, ver `035-recurring-billing.md`).

## `Invoice` — Fatura

Exposta como CRUD mínimo dentro de `033-accounts-receivable.md` (D260 — pré-requisito `NOT NULL`
de Conta a Receber).

```yaml
Invoice:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    invoice_number: { type: string, description: "`numero_fatura`." }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id` — um dos dois (trip_id/delivery_id) é obrigatório." }
    delivery_id: { $ref: "../components/schemas.md#/UUID", description: "`entrega_id` — faturamento por entrega individual (multi-drop)." }
    client_id: { $ref: "../components/schemas.md#/UUID", description: "`cliente_id`." }
    total_value: { $ref: "../components/schemas.md#/Money", description: "`valor_total` — D100, imutável após emitida; correção via Estorno (D266)." }
    issue_date: { type: string, format: date, description: "`data_emissao`." }
    payment_method_id: { $ref: "../components/schemas.md#/UUID", description: "`forma_pagamento_id`." }
    status: { type: string, enum: [EMITIDA, CANCELADA], readOnly: true }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, invoice_number, client_id, total_value, issue_date, payment_method_id, status, audit]
```

## `AccountsReceivable` — Conta a Receber

```yaml
AccountsReceivable:
  type: object
  description: "Sub-recurso de Invoice — `fatura_id NOT NULL` fisicamente, nunca criado fora de uma Fatura."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    installment_number: { type: integer, description: "`numero_parcela`." }
    value: { $ref: "../components/schemas.md#/Money", description: "`valor`." }
    due_date: { type: string, format: date, description: "`data_vencimento`." }
    received_at: { type: string, format: date-time, readOnly: true, description: "`data_recebimento`." }
    status: { type: string, enum: [PENDENTE, VENCIDA, RECEBIDA, CONCILIADA], readOnly: true, description: "D264 — nunca via PATCH." }
  required: [id, installment_number, value, due_date, status]
```

## `AccountsPayable` — Conta a Pagar

```yaml
AccountsPayable:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    supplier_id: { $ref: "../components/schemas.md#/UUID", description: "`fornecedor_id`." }
    cost_center_id: { $ref: "../components/schemas.md#/UUID", description: "`centro_custo_id`." }
    origin: { type: string, enum: [VIAGEM, ORDEM_SERVICO, ABASTECIMENTO, COMPRA, AJUSTE_MANUAL], description: "`origem` — D099, sempre explícita." }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id` — obrigatório quando origin = VIAGEM." }
    maintenance_order_id: { $ref: "../components/schemas.md#/UUID", description: "`ordem_servico_id` — obrigatório quando origin = ORDEM_SERVICO." }
    value: { $ref: "../components/schemas.md#/Money", description: "`valor`." }
    due_date: { type: string, format: date, description: "`data_vencimento`." }
    chart_of_accounts_id: { $ref: "../components/schemas.md#/UUID", description: "`plano_contas_id`." }
    status: { type: string, enum: [LANCADA, AGUARDANDO_APROVACAO, APROVADA, PAGA, CONCILIADA, REJEITADA], readOnly: true, description: "D264 — nunca via PATCH. Sem estado CANCELADA (D273) — desfecho negativo é REJEITADA." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, supplier_id, cost_center_id, origin, value, due_date, chart_of_accounts_id, status, audit]
```

## `ExpenseApproval` — Aprovação de Despesa

```yaml
ExpenseApproval:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    decision: { type: string, enum: [APROVADO, REJEITADO], readOnly: true, description: "`decisao`." }
    justification: { type: string, description: "`justificativa` — obrigatória quando decision = REJEITADO." }
    actor_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`ator_id`." }
    decided_at: { type: string, format: date-time, readOnly: true, description: "`data_hora`." }
  required: [id, decision, actor_id, decided_at]
```

## `ExpenseAllocation` — Rateio de Despesa

```yaml
ExpenseAllocation:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    cost_center_id: { $ref: "../components/schemas.md#/UUID", description: "`centro_custo_id` — um dos dois (cost_center_id/trip_id) é obrigatório." }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id`." }
    criterion: { type: string, enum: [KM_RODADO, NUMERO_VIAGENS, PESO_TRANSPORTADO], description: "`criterio`." }
    allocated_value: { $ref: "../components/schemas.md#/Money", description: "`valor_rateado`." }
  required: [id, criterion, allocated_value]
```

## `ChartOfAccounts` — Plano de Contas

```yaml
ChartOfAccounts:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    account_code: { type: string, description: "`codigo_contabil` — único por tenant." }
    name: { type: string, description: "`nome`." }
    type: { type: string, enum: [RECEITA, DESPESA], description: "`tipo`." }
    parent_id: { $ref: "../components/schemas.md#/UUID", description: "`categoria_pai_id` — nunca cria ciclo (validado na aplicação, D184)." }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, account_code, name, type, status, audit]
```

## `BankAccount` — Conta Bancária

```yaml
BankAccount:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    bank: { type: string, description: "`banco`." }
    branch: { type: string, description: "`agencia`." }
    account_number: { type: string, description: "`numero_conta`." }
    type: { type: string, enum: [CORRENTE, POUPANCA] }
    balance: { $ref: "../components/schemas.md#/Money", readOnly: true, description: "D263 — nunca digitável, sempre derivado das movimentações/lançamentos." }
    status: { type: string, enum: [ATIVA, INATIVA] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, bank, branch, account_number, type, status, audit]
```

## `BankStatementEntry` — Lançamento de Extrato Bancário

```yaml
BankStatementEntry:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    bank_account_id: { $ref: "../components/schemas.md#/UUID", description: "`conta_bancaria_id`." }
    value: { $ref: "../components/schemas.md#/Money", description: "`valor`." }
    date: { type: string, format: date, description: "`data`." }
    raw_description: { type: string, description: "`descricao_bruta`." }
    status: { type: string, enum: [NAO_CONCILIADO, CONCILIADO], readOnly: true }
  required: [id, bank_account_id, value, date, raw_description, status]
```

## `BankReconciliation` — Conciliação Bancária

```yaml
BankReconciliation:
  type: object
  description: "Aponta para exatamente um alvo: accounts_payable_id XOR accounts_receivable_id."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    bank_statement_entry_id: { $ref: "../components/schemas.md#/UUID", description: "`lancamento_extrato_id`." }
    accounts_payable_id: { $ref: "../components/schemas.md#/UUID", description: "`conta_pagar_id`." }
    accounts_receivable_id: { $ref: "../components/schemas.md#/UUID", description: "`conta_receber_id`." }
    divergence: { type: boolean, description: "`divergencia`." }
    reconciled_at: { type: string, format: date-time, readOnly: true, description: "`data_hora`." }
  required: [id, bank_statement_entry_id, divergence, reconciled_at]
```

## `FinancialReversal` — Estorno Financeiro

```yaml
FinancialReversal:
  type: object
  description: "D266 — mecanismo único de correção pós-conciliação/pagamento/recebimento. Aponta para exatamente um alvo: invoice_id XOR accounts_payable_id XOR accounts_receivable_id."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    invoice_id: { $ref: "../components/schemas.md#/UUID" }
    accounts_payable_id: { $ref: "../components/schemas.md#/UUID" }
    accounts_receivable_id: { $ref: "../components/schemas.md#/UUID" }
    value: { $ref: "../components/schemas.md#/Money", description: "`valor`." }
    reason: { type: string, description: "`motivo`." }
    reversed_at: { type: string, format: date-time, readOnly: true, description: "`data_hora`." }
  required: [id, value, reason, reversed_at]
```

## `TripFinancialsView` — Financeiro da Viagem (leitura, D262/D268)

**Não é um schema novo** — `Trip.financials` (`TripFinancials`, `components/trip-schemas.md`, Lote
4) e `Trip.snapshots.predicted_revenue_snapshot` (`TripSnapshots`, mesmo arquivo) já têm todos os
campos. `TripFinancialsView` é a **mesma estrutura reagrupada** para a resposta dedicada de
`GET /viagens/{id}/financeiro` (`038-financial-trip.md`) — nunca uma segunda fonte de verdade (D268
— API financeira não cria Read Model novo, só apresenta o que `Trip` já expõe em outro formato).

```yaml
TripFinancialsView:
  type: object
  properties:
    predicted_revenue: { type: string, readOnly: true, description: "= `Trip.snapshots.predicted_revenue_snapshot` (`receita_prevista_snapshot`), fixada na Aprovação da Cotação." }
    actual_revenue: { type: string, readOnly: true, description: "= `Trip.financials.actual_revenue` (`receita_realizada`), fixada quando `financial_status = RECEBIDA`." }
    predicted_cost: { type: string, readOnly: true, description: "= `Trip.financials.predicted_cost`." }
    actual_cost: { type: string, readOnly: true, description: "= `Trip.financials.actual_cost` — acumulado via `CustoRealizadoAtualizado` (Abastecimento/OS rateada/pedágio)." }
    predicted_margin: { type: string, readOnly: true, description: "= `Trip.financials.predicted_margin`." }
    actual_margin: { type: string, readOnly: true, description: "= `Trip.financials.actual_margin` — só definitivo quando a Viagem atinge ENCERRADA (D019)." }
    financial_deviation: { type: string, readOnly: true, description: "= `Trip.financials.financial_deviation` (Margem Realizada − Margem Prevista)." }
    financial_status: { type: string, enum: [AGUARDANDO_FATURAMENTO, FATURADA, AGUARDANDO_RECEBIMENTO, RECEBIDA], readOnly: true, description: "= `Trip.status.financial` (`018-trip-status.md`)." }
  required: [financial_status]
```

## `SubscriptionPlan` — Plano (bounded context `subscription`, D272)

```yaml
SubscriptionPlan:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    codigo: { type: string }
    name: { type: string, description: "`nome`." }
    base_price: { $ref: "../components/schemas.md#/Money", description: "`preco_base`." }
    status: { type: string, enum: [ATIVO, INATIVO], readOnly: true }
  required: [id, codigo, name, base_price, status]
```

## `Subscription` — Assinatura (bounded context `subscription`, D272)

```yaml
Subscription:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    plan_id: { $ref: "../components/schemas.md#/UUID", description: "`plano_id`." }
    status: { type: string, enum: [TRIAL, ATIVA, CANCELADA, SUSPENSA], readOnly: true, description: "Enum físico real — mais restrito que a máquina conceitual de `flows/001-ONBOARDING.md` (D272-nota)." }
    trial_starts_at: { type: string, format: date, readOnly: true, description: "`data_inicio_trial`." }
    trial_ends_at: { type: string, format: date, readOnly: true, description: "`data_fim_trial`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, plan_id, status, audit]
```

## `RecurringCharge` — Cobrança Recorrente (bounded context `billing`, D272)

```yaml
RecurringCharge:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    subscription_id: { $ref: "../components/schemas.md#/UUID", description: "`assinatura_id`." }
    value: { $ref: "../components/schemas.md#/Money", description: "`valor`." }
    currency: { type: string, readOnly: true, description: "`moeda` — BRL hoje, campo pronto para multi-moeda." }
    due_date: { type: string, format: date, description: "`data_vencimento`." }
    status: { type: string, enum: [PENDENTE, PAGA, FALHOU, CANCELADA], readOnly: true }
  required: [id, subscription_id, value, currency, due_date, status]
```

## Como este documento cresce

Adiantamento/Haver do Motorista (`financial.advance.*`/`.driver_balance.*`) não têm schema aqui —
RBAC existe, tabela física não (D190, fora de escopo desde Sprint 09). `posicoes_caixa` (Read Model
de Posição de Caixa) não ganha schema de escrita — só leitura, ver `036-bank-accounts.md`.
