# docs/backend/financeiro — Sprint 11, Lote 6 (Financeiro)

Documentação de implementação do bounded context `financial` — o dinheiro do tenant (D272: nunca
`subscription`/`billing`, o SaaS da própria plataforma). Escopo confirmado pelo usuário: Contas a
Pagar, Contas a Receber, Plano de Contas, Conta Bancária, Centro de Custo (já existente, Lote 3),
Fatura, Relação Financeira da Viagem.

| Documento | Cobre |
|---|---|
| [`PAYABLE_IMPLEMENTATION.md`](./PAYABLE_IMPLEMENTATION.md) | `AccountsPayable` (Contas a Pagar), `ExpenseApproval`, `ExpenseAllocation` (Rateio) |
| [`RECEIVABLE_IMPLEMENTATION.md`](./RECEIVABLE_IMPLEMENTATION.md) | `AccountsReceivable` (Contas a Receber) |
| [`INVOICE_IMPLEMENTATION.md`](./INVOICE_IMPLEMENTATION.md) | `Invoice` (Fatura) |
| [`REFERENCE_DATA_IMPLEMENTATION.md`](./REFERENCE_DATA_IMPLEMENTATION.md) | `ChartOfAccounts` (Plano de Contas), `BankAccount` (Conta Bancária), `PaymentMethod` (interno) |
| [`REVERSAL_IMPLEMENTATION.md`](./REVERSAL_IMPLEMENTATION.md) | `FinancialReversal` (Estorno) |
| [`TRIP_FINANCIALS_IMPLEMENTATION.md`](./TRIP_FINANCIALS_IMPLEMENTATION.md) | `GET /viagens/{id}/financeiro` (D262, vive em `freight`) |

Tudo em `modules/financial/` — RBAC `financial.*` (§7.18), exceto a Relação Financeira da Viagem
(D389, vive em `modules/freight/`).

## Fora de escopo deste lote (D385)

Conciliação Bancária (`lancamentos_extrato_bancario`/`conciliacoes_bancarias`/
`GET .../extrato`) e Posição de Caixa (`posicoes_caixa`) — nenhuma das duas está na lista de
Agregados do kickoff; `032`/`033` já documentam `PAGA→CONCILIADA`/`RECEBIDA→CONCILIADA` como
"Externa, fora de escopo" (mesmo tratamento de Coleta/Romaneio no Lote 5). Contas a Pagar/Receber
neste lote nunca alcançam `CONCILIADA` via API.

## Forma de Pagamento — sem endpoint HTTP (D386)

`formas_pagamento` é FK `NOT NULL` de `faturas.forma_pagamento_id`, mas não tem contrato de API
nem RBAC próprio. Implementada como tabela + Repository interno, seed direto nos testes — mesmo
padrão de D363 (Categoria de Veículo, Lote 4).

## Auditorias pedidas explicitamente pelo usuário antes de fechar o lote

1. **Custo Realizado é sempre derivado, nunca editável diretamente** — criar/excluir Contas a Pagar
   com `origin=VIAGEM` altera `viagens.custo_realizado` automaticamente (via Rateio de Despesa,
   D390); nenhum endpoint aceita `custo_realizado` diretamente. Ver
   [`PAYABLE_IMPLEMENTATION.md`](./PAYABLE_IMPLEMENTATION.md).
2. **Histórico financeiro completo, sem transições silenciosas** — toda mudança de status de Conta
   a Pagar/Receber grava exatamente uma linha em `contas_pagar_status_history`/
   `contas_receber_status_history`.
3. **Estorno nunca reverte o estado original** — corrigir um lançamento `PAGA`/`RECEBIDA`/`EMITIDA`
   via Estorno preserva o status original; o Estorno é só um registro de correção paralelo. Ver
   [`REVERSAL_IMPLEMENTATION.md`](./REVERSAL_IMPLEMENTATION.md).
4. **Permissões por campo, primeiro uso significativo** — `GET /viagens/{id}/financeiro` mascara
   `predicted_*`/`actual_*`/`margin`/`deviation` independentemente conforme
   `financial.trip_predicted_value.view`/`.trip_actual_value.view`/`.trip_margin.view`. Ver
   [`TRIP_FINANCIALS_IMPLEMENTATION.md`](./TRIP_FINANCIALS_IMPLEMENTATION.md).

## Cross-module Application→Application (D390)

Primeira vez neste backend: Handlers de `financial` chamam
`modules.freight.application.trip_internal_transitions.TripInternalTransitions` diretamente
(nunca `freight.infrastructure`/`.interfaces`) para atualizar `Trip.custo_realizado`/avançar
`status_financeiro` — mesmo formato "consumidor futuro de evento, síncrono porque nenhum EventBus
real está religado" de D247/D375, estendido de cross-*layer* para cross-*module*.

## Colunas de auditoria retrofitadas (D391)

`contas_pagar`/`faturas`/`plano_contas`/`contas_bancarias` ganham o bloco padrão de 6 colunas
(`criado_em`/`criado_por`/`atualizado_em`/`atualizado_por`/`excluido_em`/`excluido_por`) — a DDL
congelada tinha, no máximo, `criado_em` sozinho, mas os schemas exigem `audit: AuditMetadata`
completo e/ou D219 soft delete. `contas_receber`/`aprovacoes_despesa`/`rateios_despesa`/
`estornos_financeiros` não foram tocadas — seus schemas nunca prometeram `audit`.

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation +
auditoria comprovados por teste — mais as quatro auditorias explícitas acima.

## `AccountsPayable.status = LANCADA` nunca observável via HTTP (D395)

A alçada (`AGUARDANDO_APROVACAO`/`APROVADA`) é derivada dentro do próprio `POST /contas-pagar`,
sem nenhum gatilho posterior separado (diferente de `RASCUNHO→PLANEJADA`, Trip/Lote 5, cujo gatilho
é a primeira alocação de recurso). Consequência: `PATCH`/`DELETE` — documentados em
`032-accounts-payable.md` como válidos só em `LANCADA` — ficam inalcançáveis via API pública neste
lote. A suíte de integração prova o recálculo de `Trip.custo_realizado` na remoção de uma Conta a
Pagar manipulando `status` direto no banco antes do `DELETE` real, mesmo espírito de
`TripInternalTransitions` (D376).

**Nota de leitura, não é defeito da API**: `LANCADA` é um estado real do domínio — existe no Enum,
aparece na máquina de estados de `032-accounts-payable.md`, tem regras de negócio próprias
(`update()`/`soft_delete()` verificam explicitamente `status == LANCADA`) — mas nunca é observável
por um consumidor HTTP porque a resolução automática da alçada acontece de forma síncrona, dentro
do mesmo comando que cria o registro, antes de qualquer resposta ser devolvida ao cliente. Um
integrador lendo só o contrato OpenAPI pode legitimamente perguntar "por que `DELETE` nunca
funciona?" — a resposta é esta: certos estados existem no domínio mas não são necessariamente
observáveis por consumidores HTTP, por causa da resolução síncrona do comando que os deriva. Vale a
mesma leitura para qualquer transição futura desenhada no mesmo formato (derivação automática sem
gatilho externo separado).

## Achados deste lote (Sprint 11, Lote 6)

`alembic upgrade head` criou as 8 tabelas novas (`plano_contas`/`contas_bancarias`/`formas_
pagamento`/`contas_pagar`/`contas_pagar_status_history`/`aprovacoes_despesa`/`rateios_despesa`/
`faturas`/`contas_receber`/`contas_receber_status_history`/`estornos_financeiros`) contra o
Postgres portátil sem nenhum bug de DDL novo — os três falsos-positivos recorrentes de
autogenerate contra tabelas particionadas (`logs_auditoria_default`/`leituras_hodometro_default`/
`viagem_status_history_default`) foram removidos manualmente da migration antes de aplicar, mesmo
tratamento de todo lote anterior desde a Sprint 09. `ruff`/`mypy --strict`/`lint-imports` passaram
limpos na primeira execução, sem nenhum achado a corrigir — nenhuma coluna `GENERATED` nova neste
lote (`margem_realizada`/`desvio_financeiro` são recalculadas pela aplicação, D392), então o bug de
mapeamento `Computed(...)` do Lote 5 (D382) não se repetiu. O único achado real de implementação foi
D395 (acima), encontrado ao desenhar a Auditoria #1 do usuário e não por uma falha de teste depois —
`AccountsPayable.create()` já tinha sido escrito para derivar o status instantaneamente; o gap de
alcançabilidade via `PATCH`/`DELETE` foi identificado e documentado antes de escrever o teste, não
descoberto por um teste falhando. A suíte fecha em **111 passed, 0 failed** (93 acumulados + 18
novos de Financeiro; Redis/RabbitMQ/MinIO continuam fora do ambiente de build, mesma lacuna de
infraestrutura de todo lote anterior). As quatro auditorias explícitas do usuário foram todas
verificadas por teste real contra HTTP + Postgres:

1. **Totais derivados nunca editáveis diretamente** — `TestTotalsDerivedFromAllocationAudit`: criar
   duas Contas a Pagar `origin=VIAGEM` soma (nunca substitui) `Trip.custo_realizado`; remover uma
   recalcula para a soma restante; um `PATCH` com um campo `actual_cost`/`custo_realizado`
   "estranho" no corpo é silenciosamente ignorado (`extra=\"ignore\"`).
2. **Histórico completo, sem transições silenciosas** — `TestStatusHistoryAudit`: a derivação
   `LANCADA→AGUARDANDO_APROVACAO` na criação já grava sua própria linha (`observacao=\"LANCADA\"`
   quando o destino é `APROVADA`); `approve`/`pay`/criação de Conta a Receber/`confirm-receipt`
   cada um soma exatamente +1 linha, nunca 0, nunca 2.
3. **Estorno nunca reverte** — `TestEstornoNeverRevertsAudit`: uma Conta a Pagar `PAGA` estornada
   continua `PAGA` depois do Estorno, sem nenhuma linha nova em `contas_pagar_status_history`; o
   Estorno existe como sua própria trilha, consultável isoladamente por `accounts_payable_id`.
4. **Permissões por campo** — `TestTripFinancialsFieldLevelRbacAudit`: ator com só `financial.
   trip_predicted_value.view` (+`freight.trip.view`) recebe `predicted_*` populado e `actual_*`/
   `margin`/`deviation` como `null`; ator sem nenhuma das três permissões de valor recebe `403`
   mesmo tendo `freight.trip.view`; ator com permissão de valor mas sem `freight.trip.view` também
   recebe `403`.

## Decisões

D384–D395 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: Sprint 11 Lote 7 — Fiscal.
