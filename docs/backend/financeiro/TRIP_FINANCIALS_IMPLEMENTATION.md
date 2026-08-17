# TRIP_FINANCIALS_IMPLEMENTATION.md — `GET /viagens/{id}/financeiro`

D262/D268/D389 — bounded context proprietário **`freight`**, não `financial` (o dono do dado é
quem o domínio diz que é, mesmo quando o endpoint fica tematicamente no lote de outro módulo). Vive
em `modules/freight/interfaces/api/trip_financials_router.py` + uma Query nova em
`modules/freight/application/queries/get_trip_financials.py` — **não** um Read Model novo (D268):
lê os mesmos campos já expostos em `Trip.financials`/`Trip.snapshots`, só reagrupados.

## Auditoria #4 do usuário — permissões por campo

Três permissões (`financial.*`, RBAC de `financial` mesmo o endpoint vivendo em `freight` — RBAC
segue o dado sensível, não o Controller) controlam três grupos de campos independentemente:

| Permissão | Controla |
|---|---|
| `financial.trip_predicted_value.view` | `predicted_revenue`, `predicted_cost`, `predicted_margin` |
| `financial.trip_actual_value.view` | `actual_revenue`, `actual_cost` |
| `financial.trip_margin.view` | `actual_margin`, `financial_deviation` |

Sem a permissão correspondente, o grupo retorna `null` — nunca omitido do schema, nunca `403`
parcial (mesmo padrão de `maintenance.work_order.view_cost`, Lote 6 do OpenAPI). `financial_status`
não exige nenhuma das três (já público via `freight.trip.view`). O endpoint inteiro exige
`freight.trip.view` **e** ao menos uma das três — `403` só se nenhuma das quatro permissões
estiver presente.

## Erros de domínio

`FREIGHT_TRIP_NOT_FOUND` (404) — mesmo código de `014-trips.md`, este endpoint não inventa um
namespace de erro próprio (é uma leitura de Viagem, D262).

## Auditoria e tenant isolation

Somente leitura — nenhuma escrita própria. Tenant isolation herdado de
`SqlAlchemyTripRepository.get_by_id` (já filtra por `tenant_id`, Lote 5).
