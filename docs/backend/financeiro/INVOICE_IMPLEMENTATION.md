# INVOICE_IMPLEMENTATION.md — Fatura

Fonte: `033-accounts-receivable.md` seção `Invoice` (D260 — CRUD mínimo, pré-requisito de Contas a
Receber, não um arquivo próprio).

## `POST /faturas` — cria Fatura + parcelas numa única transação

Exatamente um de `trip_id`/`delivery_id` (`ck_faturas_origem`, 400 caso contrário).

**Precondição real, D388**: consulta diretamente (cross-module read, D356)
`ProofOfDeliveryRepository` (`freight`, Lote 5) — precisa existir ao menos um Canhoto `REGISTRADO`
entre as Entregas da Viagem — e `Trip.status_fiscal` — precisa ser diferente de `PENDENTE`/
`CTE_CANCELADO` (ou seja, ao menos `CTE_EMITIDO`). Sem as duas condições,
`FINANCIAL_INVOICE_MISSING_PRECONDITION` (409). Diferente das transições do Lote 5 que precisaram
de método interno simulado (D376), aqui as duas fontes já existem de verdade — nunca simulado.

**Efeito colateral (D390)**: quando `trip_id` presente, chama
`TripInternalTransitions.record_financial_transition(trip_id, FATURADA, now)` —
`AGUARDANDO_FATURAMENTO → FATURADA`, mesma dimensão Financeira já `readOnly` em `018-trip-
status.md`. `financial` nunca escreve `status_operacional`.

## `commands/cancel`

`EMITIDA → CANCELADA` — único comando real de Fatura (D273: aqui "cancelar" existe de fato).
Reabre a necessidade de reemissão fiscal (`009-FISCAL.md`, lote futuro) — não detalhado aqui.

## Sem `PATCH`/`DELETE`

`valor_total` imutável após emitida (D100) — correção via `FinancialReversal`
(`REVERSAL_IMPLEMENTATION.md`), nunca edição direta.

## Colunas de auditoria (D391)

`faturas` ganha o bloco padrão de 6 colunas — a DDL congelada só tinha `criado_em`.

## Erros de domínio

`FINANCIAL_INVOICE_NOT_FOUND` (404), `FINANCIAL_INVOICE_ORIGIN_MISMATCH` (400), `FINANCIAL_UNKNOWN_
CLIENT_ID`/`_PAYMENT_METHOD_ID`/`_TRIP_ID`/`_DELIVERY_ID` (422), `FINANCIAL_INVOICE_MISSING_
PRECONDITION` (409), `FINANCIAL_INVOICE_INVALID_STATUS` (409, `cancel` fora de `EMITIDA`).

## Auditoria e tenant isolation

Criação/cancelamento gravam `logs_auditoria`. `SqlAlchemyInvoiceRepository` filtra por
`get_current_tenant_id()`.
