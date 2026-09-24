# 032 — Accounts Payable (Contas a Pagar)

Bounded context proprietário: `financial` (D215, D261). Máquina de estados canônica em
[`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) seção "Máquina de Estados — Contas a
Pagar", atributos/DDL em
[`../database/relational/006-financeiro.md`](../database/relational/006-financeiro.md), RBAC em
`RBAC_MATRIX.md` §7.18 — todos lidos por completo antes de escrever este documento (D200 aplicado à
API).

## D273 — "cancelar" do pedido não é um estado real

`contas_pagar_status_enum` = `LANCADA`, `AGUARDANDO_APROVACAO`, `APROVADA`, `PAGA`, `CONCILIADA`,
`REJEITADA` — **sem `CANCELADA`**. O desfecho negativo real é `REJEITADA` (`commands/reject`), não
um `commands/cancel` inventado. `DELETE` (abaixo) cobre o caso de "eu lancei errado antes de
qualquer aprovação", que é a intenção mais próxima de "cancelar" que o domínio realmente suporta.

## `GET /api/v1/contas-pagar`

**Segurança**: `bearerAuth` + `financial.payable.view`.

**Query parameters**: `page`/`limit`, `search` (nenhum campo de texto livre óbvio — omitido),
`status`, `origin` (`origem`), `supplier_id` (`fornecedor_id`), `cost_center_id`
(`centro_custo_id`), `trip_id` (`viagem_id`), `due_date__gte`/`__lte` (`data_vencimento`).
**Reconciliado (Lote Financeiro, Parte 2.1)**: `vehicle_id` (`veiculo_tracionador_id`),
`chart_of_accounts_id` (`plano_contas_id`), `accounting_period` (`competencia`, igualdade exata —
sempre o primeiro dia do mês, mesma convenção da criação) — as três dimensões formalizadas na
Parte 1 estavam gravadas mas não eram consultáveis; gap fechado aqui, sem endpoint novo.

**Responses**: `200` (`Pagination` de `AccountsPayable`, `financial-schemas.md`), `401`, `403`,
`500`.

**Visibilidade de valores**: ao contrário de Manutenção (D267-nota), `financial.payable.view` já
inclui `value` — não há um `.view_value` separado nesta seção da matriz; a granularidade fina de
valores fica concentrada em `financial.trip_predicted_value.view`/`.trip_actual_value.view`
(`038-financial-trip.md`).

## `GET /api/v1/contas-pagar/{id}`

**Responses**: `200` (`AccountsPayable`), `401`, `403`, `404`, `500`.

## `POST /api/v1/contas-pagar`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          supplier_id: { $ref: "components/schemas.md#/UUID" }
          cost_center_id: { $ref: "components/schemas.md#/UUID" }
          origin: { type: string, enum: [VIAGEM, ORDEM_SERVICO, ABASTECIMENTO, COMPRA, AJUSTE_MANUAL] }
          trip_id: { $ref: "components/schemas.md#/UUID" }
          maintenance_order_id: { $ref: "components/schemas.md#/UUID" }
          value: { type: string }
          due_date: { type: string, format: date }
          chart_of_accounts_id: { $ref: "components/schemas.md#/UUID" }
        required: [supplier_id, cost_center_id, origin, value, due_date, chart_of_accounts_id]
```

`origin = VIAGEM` exige `trip_id`; `origin = ORDEM_SERVICO` exige `maintenance_order_id` —
`ck_contas_pagar_origem_especifica` (D099, "todo lançamento tem origem explícita"), `400` caso
contrário. `status` nasce sempre `LANCADA`.

**Segurança**: `financial.payable.create`. **Idempotency-Key**: aceita e com enforcement real
(Reconciliado, V1 Operational Hardening Parte 6, `core/idempotency/` — lançamento de despesa é uma
das operações críticas do módulo; "obrigatório" era documentado desde D211 mas nunca de fato
aplicado antes desta rodada, D418).

**Responses**: `201` (`AccountsPayable`), `400`, `401`, `403`, `404` (Fornecedor/Centro de Custo/
Plano de Contas/Viagem/OS não existe), `500`.

## `PATCH /api/v1/contas-pagar/{id}`

D229 — parcial (`supplier_id`, `cost_center_id`, `value`, `due_date`, `chart_of_accounts_id`).
**Nunca `status`** (D264). Só permitido em `status = LANCADA` — depois de `AGUARDANDO_APROVACAO`, o
valor já está sob análise e não pode ser silenciosamente trocado (D100 — imutável após submetido a
aprovação; reforçado na aplicação).

**Segurança**: `financial.payable.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409` —
`FINANCIAL_PAYABLE_INVALID_STATUS`, `500`.

## `DELETE /api/v1/contas-pagar/{id}`

**D219 — soft delete.** Só em `status = LANCADA` (equivalente ao "cancelar antes de qualquer
aprovação" — ver D273).

**Segurança**: `financial.payable.edit` — `RBAC_MATRIX.md` §7.18 não tem `.payable.delete`;
reaproveitado `.edit` por precedente direto de D240/D250/D260 (Lotes 4-6), lacuna documentada.

**Responses**: `204`, `401`, `403`, `404`, `409` — `FINANCIAL_PAYABLE_DELETE_INVALID_STATUS`, `500`.

## Máquina de estados — comandos

| De | Para | Comando | RBAC |
|---|---|---|---|
| `LANCADA` | `AGUARDANDO_APROVACAO` | — | **Derivada** |
| `LANCADA` | `APROVADA` | — | **Derivada** |
| `AGUARDANDO_APROVACAO` | `APROVADA` | `commands/approve` | `financial.payable.approve` |
| `AGUARDANDO_APROVACAO` | `REJEITADA` | `commands/reject` | `financial.payable.reject` |
| `APROVADA` | `PAGA` | `commands/pay` | `financial.payable.pay` |
| `PAGA` | `CONCILIADA` | — | **Externa** (`037-bank-reconciliation.md`) |

### `LANCADA → AGUARDANDO_APROVACAO` / `LANCADA → APROVADA` — Derivada, não um comando

`003-MANUTENCAO.md`/`018-trip-status.md` já estabeleceram o padrão: quando a transição depende só
de comparar um valor contra uma alçada configurada (nunca uma ação de ator), ela é automática. Aqui
é textual em `005-FINANCEIRO.md`: "Valor da despesa excede a alçada do lançador" →
`AGUARDANDO_APROVACAO`; "Valor dentro da alçada" → `APROVADA` (aprovação automática). A alçada em si
é consultada em `settings`/Administração, nunca duplicada aqui (mesmo princípio de D255, Lote 6) —
ainda sem endpoint próprio (mesma lacuna de dependência já registrada em `028-maintenance-
approvals.md`).

### `commands/approve` / `commands/reject`

Cria um registro em `ExpenseApproval` (`aprovacoes_despesa`) e transiciona a Conta a Pagar.
`justification` obrigatória em `reject` (D010). **Reconciliado (V1 Operational Hardening, Parte
1)**: `reject` remove o Rateio (`rateios_despesa`) desta Conta a Pagar e recalcula
`viagens.custo_realizado` da Viagem afetada quando `origin=VIAGEM` (ou `ORDEM_SERVICO` com Viagem
associada) — mesmo mecanismo de `DELETE /contas-pagar/{id}` (D390/D393). `approve` nunca muda
`custo_realizado` — o custo já contava desde o lançamento (regime de competência,
`006-financeiro.md`).

**Segurança**: `financial.payable.approve` / `.reject`. **Idempotency-Key**: aceita, sem
enforcement real ainda — gap conhecido (só `POST` de criação e `commands/pay` ganharam a
implementação real nesta rodada, V1 Operational Hardening Parte 6, `IDEMPOTENCY.md`).

```yaml
requestBody:
  required: false
  content:
    application/json:
      schema:
        type: object
        properties:
          justification: { type: string }
```

(`justification` passa a `required` no corpo apenas para `commands/reject`.)

**Responses**: `200` (`AccountsPayable`, D238), `400`, `401`, `403`, `404`, `409` —
`FINANCIAL_PAYABLE_INVALID_TRANSITION`, `500`.

## `GET /api/v1/contas-pagar/{id}/aprovacoes`

Histórico de decisões (normalmente 0 ou 1 registro — múltiplos níveis são um requisito futuro, mesmo
princípio de `nivel` em `aprovacoes_custo`/Manutenção, mas `aprovacoes_despesa` não tem essa coluna
hoje — não inventada aqui, D101/D102).

**Segurança**: `financial.payable.view`. **Responses**: `200` (`Pagination` de `ExpenseApproval`),
`401`, `403`, `404`, `500`.

## `commands/pay`

`APROVADA → PAGA`. Pagamento efetuado (PIX/boleto/transferência) — **este é o "pagamento" pedido no
kickoff**; não existe `POST /pagamentos` separado (`contas_pagar_status_history` já registra a
transição, mesmo padrão de `026-maintenance-orders.md`).

**Segurança**: `financial.payable.pay`. **Idempotency-Key**: aceita e com enforcement real
(Reconciliado, V1 Operational Hardening Parte 6, `core/idempotency/` — pagamento é criticamente
sensível a duplicação; "obrigatório" era documentado desde D211 mas nunca de fato aplicado antes
desta rodada, D418).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          bank_account_id: { $ref: "components/schemas.md#/UUID" }
        required: [bank_account_id]
```

**Responses**: `200` (`AccountsPayable`), `400`, `401`, `403`, `404`, `409` —
`FINANCIAL_PAYABLE_INVALID_TRANSITION`, `500`.

## `PAGA → CONCILIADA` — externa, fora de escopo deste endpoint

Acontece via `037-bank-reconciliation.md` (`commands/confirm` sobre `BankReconciliation`), nunca por
um comando direto em `contas-pagar` — a Conta a Pagar é o **alvo** da conciliação, não quem a
inicia (D225-style ownership).

## Rateio (`ExpenseAllocation`)

`rateios_despesa` alimenta `viagens.custo_realizado` (Financeiro Operacional, D262) — exposto aqui
como sub-recurso somente leitura; a criação de rateio acontece internamente quando a Conta a Pagar é
lançada com `origin = ORDEM_SERVICO`/`VIAGEM` (rateio automático), nunca via um `POST` livre neste
lote (RBAC tem `financial.cost_allocation.create`, mas o pedido do usuário não incluiu um fluxo de
rateio manual — documentado como dependência a esclarecer, não inventado).

### `GET /api/v1/contas-pagar/{id}/rateios`

**Segurança**: `financial.cost_allocation.view`. **Responses**: `200` (`Pagination` de
`ExpenseAllocation`), `401`, `403`, `404`, `500`.

## Fora de escopo, não esquecido

- **Adiantamento/Haver do Motorista** (`financial.advance.*`/`.driver_balance.*`): RBAC existe,
  tabela física não (D190) — sem endpoint.
- **Rateio manual** (`POST /rateios`): RBAC `financial.cost_allocation.create` existe, mas o fluxo
  de criação manual (fora do rateio automático por origem) não foi detalhado neste lote.

## Como este documento cresce

Quando Adiantamento/Haver forem modelados (retomando D190), este documento ganha uma seção de
rateio envolvendo motorista — hoje `rateios_despesa.centro_custo_id`/`.viagem_id` já cobrem os dois
alvos documentados.
