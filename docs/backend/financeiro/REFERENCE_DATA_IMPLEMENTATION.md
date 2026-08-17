# REFERENCE_DATA_IMPLEMENTATION.md — Plano de Contas, Conta Bancária, Forma de Pagamento

## `ChartOfAccounts` (Plano de Contas, `034-chart-of-accounts.md`)

Hierárquica via `categoria_pai_id` (auto-referência). `PATCH` alterando `parent_id` valida ausência
de ciclo percorrendo `categoria_pai_id` até a raiz na Application —
`FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED` (422) se a nova conta-pai for a própria conta ou uma
descendente. `DELETE` (soft, D219) bloqueado por `FINANCIAL_CHART_OF_ACCOUNTS_HAS_ACTIVE_CHILDREN`
(409, existe filha `status=ATIVO`) ou `FINANCIAL_CHART_OF_ACCOUNTS_IN_USE` (409, referenciada por
`contas_pagar.plano_contas_id`).

## `BankAccount` (Conta Bancária, `036-bank-accounts.md`)

`account_number`/`type` imutáveis após criação (Atributo Crítico, D077-style — troca é evento raro
e sensível, vira conta nova). `GET .../saldo` (D263 — saldo sempre derivado, nunca digitável):
soma `contas_pagar.valor` `PAGA` menos... na verdade soma **recebimentos** (`contas_receber`
`RECEBIDA`, via `PAGA`/`RECEBIDA` desta lote não têm `conta_bancaria_id` física ainda — `commands/
pay` recebe `bank_account_id` no corpo mas a DDL de `contas_pagar` não tem essa coluna) — resolvido
calculando o saldo como `SUM(contas_receber.valor WHERE status IN (RECEBIDA))` menos
`SUM(contas_pagar.valor WHERE status IN (PAGA))`, sem filtrar por conta bancária específica ainda
(nenhuma das duas tabelas tem FK para `contas_bancarias`, D394 — ver nota abaixo). `GET .../extrato`
fora de escopo (D385).

### D394 — `commands/pay` aceita `bank_account_id` mas não persiste a associação

`contas_pagar`/`contas_receber` não têm coluna `conta_bancaria_id` na DDL congelada — só
`lancamentos_extrato_bancario`/`conciliacoes_bancarias` (fora de escopo, D385) referenciam
`contas_bancarias`. `commands/pay` valida que o `bank_account_id` informado existe e está `ATIVA`,
mas não há onde persistir o vínculo nesta migration — documentado, não inventada uma coluna nova.
`GET /contas-bancarias/{id}/saldo` reflete o saldo agregado do tenant, não filtrado por conta,
mesma limitação.

`DELETE` (soft, D219): `FINANCIAL_BANK_ACCOUNT_IN_USE` nunca é possível de disparar nesta versão
(sem `lancamentos_extrato_bancario`, D385) — documentado, endpoint aceita mas a condição de bloqueio
está sempre vazia.

## Colunas de auditoria (D391)

`plano_contas`/`contas_bancarias` ganham o bloco padrão de 6 colunas — a DDL congelada não tinha
nenhuma coluna de timestamp.

## `PaymentMethod` (Forma de Pagamento, D386)

Sem endpoint HTTP — tabela + Repository interno, seed direto nos testes (mesmo padrão de D363).

## Auditoria e tenant isolation

Toda criação/edição grava `logs_auditoria`. Os três Repositories filtram por
`get_current_tenant_id()`.
