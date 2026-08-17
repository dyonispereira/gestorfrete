# 038 — Financial Trip (Financeiro da Viagem)

Bounded context proprietário: `freight` (D262) — **não** `financial`. Este endpoint é uma leitura
especializada que o módulo `financial` monta a partir de dados que já pertencem à Viagem (D215:
mesmo quando um endpoint "fica" tematicamente num lote de outro módulo, o dono do dado é quem o
domínio diz que é).

## D262 — Viagem continua dona dos valores da sua operação

Receita/Custo Previsto e Realizado, Margem, Desvio Financeiro — todos vivem em `viagens`
(`relational/003-operacao.md`, Lote 4) e já são expostos em `Trip.financials`/`Trip.snapshots`
(`014-trips.md`, `components/trip-schemas.md`). **Nenhuma coluna nova foi criada em `financial` para
duplicar esses valores** — `relational/006-financeiro.md` já registra essa separação
("Financeiro Operacional... nunca duplicado aqui").

## D268 — este endpoint não é um Read Model novo

`GET /viagens/{id}/financeiro` não persiste nada — é uma consulta que agrega campos já existentes de
`Trip` num formato dedicado, mais conveniente para quem só quer a visão financeira sem o restante do
payload de Viagem (referências, alocação, ocorrências). Equivalente a "abrir `GET /viagens/{id}` e
olhar só `financials`/`snapshots.predicted_revenue_snapshot`/`status.financial`" — nunca uma segunda
fonte de verdade.

## `GET /api/v1/viagens/{id}/financeiro`

**Segurança**: `bearerAuth` + combinação de três permissões distintas, cada uma controlando um
subconjunto de campos da resposta (D267 — dados financeiros sensíveis têm autorização própria,
mesmo padrão de granularidade de campo já visto em `maintenance.work_order.view_cost`, Lote 6):

| Permissão | Controla |
|---|---|
| `financial.trip_predicted_value.view` | `predicted_revenue`, `predicted_cost`, `predicted_margin` |
| `financial.trip_actual_value.view` | `actual_revenue`, `actual_cost` |
| `financial.trip_margin.view` | `actual_margin`, `financial_deviation` |

Sem a permissão correspondente, o grupo de campos retorna `null` — mesmo padrão de "campo existe no
schema, valor omitido por RBAC" já usado em `026-maintenance-orders.md`. `financial_status` não
exige nenhuma das três (é o Status Financeiro já público via `freight.trip.view`, `018-trip-
status.md`).

**Responses**: `200` (`TripFinancialsView`, `financial-schemas.md`), `401`, `403` (nem uma permissão
de valor, nem `freight.trip.view`), `404`, `500`.

## Nenhum comando aqui

Este documento é **só leitura** — todo comando que altera esses valores já vive em outro lugar:

| Valor | Onde muda |
|---|---|
| `predicted_revenue` | Aprovação da Cotação — fora do escopo desta API (`freight`, lote de Cotação ainda não construído) |
| `predicted_cost` | Programação da Viagem — idem |
| `actual_cost` | `CustoRealizadoAtualizado`, consumido de `OrdemServicoFechada` (`026-maintenance-orders.md`, `commands/fechar`) e de Abastecimento (fora de escopo, `006-ABASTECIMENTO.md`) |
| `actual_revenue` | `commands/confirm-receipt` (`033-accounts-receivable.md`) |
| `financial_status` | `POST /faturas` (`033`, `AGUARDANDO_FATURAMENTO → FATURADA`) e `commands/confirm-receipt` (`AGUARDANDO_RECEBIMENTO → RECEBIDA`) |
| `predicted_margin`/`actual_margin`/`financial_deviation` | Recalculados pela aplicação a cada mudança dos valores acima (`MargemCalculada`) |

Nenhum desses é um `PATCH`/comando deste documento — reforça a regra do usuário: "Financeiro não
altera operação diretamente... Apenas reage aos eventos da Operação."

## Fora de escopo, não esquecido

- **Cotação/Programação da Viagem**: onde `predicted_revenue`/`predicted_cost` nascem — lote de
  Viagem ainda não cobriu esses estágios pré-`RASCUNHO` (`014-trips.md` começa em Viagem já criada).
- **Rateio de OS/Abastecimento incorporado ao Custo Realizado**: mecanismo já existe
  (`rateios_despesa.viagem_id`, `032-accounts-payable.md`), mas não há um endpoint que liste "quais
  lançamentos compõem o Custo Realizado desta viagem" — candidato a `GET /viagens/{id}/financeiro/
  composicao-custo` num lote futuro, não inventado agora.

## Como este documento cresce

Se o produto precisar de um detalhamento "de onde vem cada parte do Custo Realizado" (rateios de
OS + Abastecimentos + pedágios, um por um), isso é um novo endpoint aditivo, não uma mudança neste —
`TripFinancialsView` permanece o resumo agregado.
