# REVERSAL_IMPLEMENTATION.md — Estorno Financeiro

Fonte: `037-bank-reconciliation.md` seção `FinancialReversal` (D266). Mecanismo único de correção
pós-fato para Fatura/Conta a Pagar/Conta a Receber — exatamente um dos três alvos
(`ck_estornos_financeiros_alvo_exclusivo`, 400 caso contrário).

## Auditoria #3 do usuário — Estorno nunca reverte o estado original

`CreateFinancialReversalHandler` **nunca** altera `status`/`valor` do registro alvo — só insere a
linha em `estornos_financeiros`, referenciando o alvo. Uma Conta a Pagar `PAGA` estornada continua
`PAGA` (`contas_pagar_status_history` não ganha uma nova linha); o Estorno é a própria trilha,
paralela, nunca uma transição de status do original. Publica `EstornoRealizado` (já em
`EVENT_MAP.md`, D270) — documentado, não despachado a um EventBus real (nenhum módulo deste
backend publica eventos de verdade ainda, mesma situação de todo lote anterior).

## Sem `PATCH`/`DELETE`

Corrigir um Estorno errado exige um novo Estorno apontando para o mesmo alvo, nunca editar/remover
o existente (D037, mesmo princípio de todo histórico do sistema).

## Erros de domínio

`FINANCIAL_REVERSAL_TARGET_MISMATCH` (400 — zero ou mais de um alvo), `FINANCIAL_REVERSAL_TARGET_
NOT_FOUND` (404).

## Auditoria e tenant isolation

Criação grava `logs_auditoria`. `SqlAlchemyFinancialReversalRepository` filtra por
`get_current_tenant_id()`.
