# PAYABLE_IMPLEMENTATION.md — Contas a Pagar

Aggregate Root de `financial`. Fonte: `flows/005-FINANCEIRO.md` (máquina de estados),
`relational/006-financeiro.md` (DDL), `032-accounts-payable.md` (HTTP).

## Máquina de estados

`LANCADA → {AGUARDANDO_APROVACAO, APROVADA}` (derivada, comparação contra alçada — como não há
endpoint de alçada configurável neste lote, D255-style: uma constante de módulo faz o papel de
alçada até `settings` existir, documentada como placeholder) `→ {APROVADA, REJEITADA}` (comandos
`approve`/`reject`, cada um cria uma linha em `aprovacoes_despesa`) `→ PAGA` (`commands/pay`) `→
CONCILIADA` (externa, fora de escopo, D385). Sem `CANCELADA` (D273) — desfecho negativo real é
`REJEITADA`; `DELETE` cobre "lancei errado", só em `LANCADA`.

## Rateio automático (`ExpenseAllocation`, D393)

Ao criar uma Conta a Pagar com `origin ∈ {VIAGEM, ORDEM_SERVICO}`, o Handler cria uma linha em
`rateios_despesa` alocando 100% do `valor` ao alvo (`viagem_id`/`centro_custo_id`) — `criterio`
fixo (`NUMERO_VIAGENS`, placeholder D393, rateio proporcional real fora de escopo). Quando
`viagem_id` está presente, o mesmo Handler chama
`TripInternalTransitions.update_realized_cost(trip_id, novo_total, now)` (D390) — `novo_total` é a
soma de todos os `rateios_despesa.valor_rateado` daquela viagem, nunca o `valor` desta Conta a
Pagar isoladamente (uma segunda Conta a Pagar para a mesma viagem soma, não substitui).

**Auditoria #1 do usuário**: `DeleteAccountsPayableHandler` (só em `LANCADA`) remove a(s) linha(s)
de rateio associada(s) e recalcula `Trip.custo_realizado` da mesma forma — "remover item" também
atualiza o total. Nenhum endpoint aceita `custo_realizado` diretamente; o único jeito de mudá-lo é
criar/excluir uma Conta a Pagar com `origin=VIAGEM`.

## `ordem_servico_id` sem FK física (D387)

`Ordem de Serviço` (`maintenance`) não está implementada — coluna `UUID` nullable sem
`REFERENCES`, mesmo padrão de D355/D362. `origin=ORDEM_SERVICO` continua validado
(`FREIGHT`-like `ck_contas_pagar_origem_especifica` reforçado no Domain), só a integridade
referencial física fica pendente.

## Colunas de auditoria (D391)

`contas_pagar` ganha o bloco padrão de 6 colunas — a DDL congelada só tinha `criado_em`.
`AccountsPayableResponse.audit` agora reflete um `AuditMetadata` real (não omitido).

## Erros de domínio

`FINANCIAL_PAYABLE_NOT_FOUND` (404), `FINANCIAL_UNKNOWN_SUPPLIER_ID`/`_COST_CENTER_ID`/
`_CHART_OF_ACCOUNTS_ID`/`_TRIP_ID` (422 — referência inexistente), `FINANCIAL_PAYABLE_ORIGIN_
MISMATCH` (400 — `origin=VIAGEM` sem `trip_id`, etc., `ck_contas_pagar_origem_especifica`),
`FINANCIAL_PAYABLE_INVALID_STATUS` (409 — `PATCH` fora de `LANCADA`), `FINANCIAL_PAYABLE_DELETE_
INVALID_STATUS` (409), `FINANCIAL_PAYABLE_INVALID_TRANSITION` (409 — `approve`/`reject`/`pay` fora
do estado esperado), `FINANCIAL_PAYABLE_JUSTIFICATION_REQUIRED` (400 — `reject` sem
`justification`).

## Auditoria e tenant isolation

Toda criação/transição grava `logs_auditoria` (D007) e uma linha em `contas_pagar_status_history`
(D017/D018) — auditoria #2 do usuário: nenhuma transição (incluindo a derivada `LANCADA→APROVADA`)
pula essa gravação. `SqlAlchemyAccountsPayableRepository` filtra por `get_current_tenant_id()`.
