# RECEIVABLE_IMPLEMENTATION.md — Contas a Receber

Sub-recurso de `Invoice` (`fatura_id NOT NULL` fisicamente, D260 — nunca existe fora de uma
Fatura). Fonte: `033-accounts-receivable.md`.

## Máquina de estados

`PENDENTE → VENCIDA` (derivada, `data_vencimento` no passado — sem job periódico neste lote,
calculado na leitura: `status` efetivo é `VENCIDA` quando `PENDENTE` e `data_vencimento < hoje`,
mesmo raciocínio de `DriverDocument.status`/Lote 3, nunca uma coluna gravada como fonte de verdade
separada) `→ RECEBIDA` (`commands/confirm-receipt`) `→ CONCILIADA` (externa, D385).

## `commands/confirm-receipt`

**Auditoria #1 do usuário, continuação**: além de marcar a parcela `RECEBIDA`, o Handler soma
`received_value` de todas as parcelas `RECEBIDA` da Fatura e chama
`TripInternalTransitions.update_realized_revenue(trip_id, soma, now)` (D390) quando a Fatura tem
`trip_id`. Quando a **última** parcela pendente da Fatura é confirmada, chama também
`TripInternalTransitions.record_financial_transition(trip_id, RECEBIDA, now)` — mesmo evento
`RecebimentoConfirmado` já documentado em `018-trip-status.md`/`EVENT_MAP.md`.

`received_value` divergente de `value` não bloqueia a confirmação (`033` documenta isso como gerar
uma Ocorrência financeira, fora de escopo — D385-adjacent) — só registrado, nunca impede o fluxo.

## Erros de domínio

`FINANCIAL_RECEIVABLE_NOT_FOUND` (404), `FINANCIAL_RECEIVABLE_INSTALLMENT_ALREADY_EXISTS` (409,
`uq_contas_receber_fatura_id_parcela`), `FINANCIAL_RECEIVABLE_INVALID_STATUS` (409, `PATCH` fora
de `PENDENTE`/`VENCIDA`), `FINANCIAL_RECEIVABLE_INVALID_TRANSITION` (409, `confirm-receipt` fora
de `PENDENTE`/`VENCIDA`). Sem `DELETE` (RBAC não tem `.receivable.delete`, correção via Estorno).

## Auditoria e tenant isolation

Toda transição grava `logs_auditoria` e uma linha em `contas_receber_status_history`.
`SqlAlchemyAccountsReceivableRepository` filtra por `get_current_tenant_id()` via a Fatura-dona.
