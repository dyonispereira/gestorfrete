# 030 — Maintenance History (Histórico Operacional da OS)

Bounded context proprietário: `maintenance` (D215). `ordens_servico_status_history` — Histórica
(D017/D018), somente leitura (D257).

## Histórico Operacional ≠ Timeline Universal

`003-MANUTENCAO.md` cita "Timeline Universal (D022)" como capacidade transversal aplicável à OS,
combinando `OrdemServicoStatusHistory` + solicitações de peça + comentários do Mecânico + anexos —
igual ao que `019-trip-timeline.md` fez para Viagem. **Este documento não é essa Timeline.** Neste
lote, Solicitação de Peça/Comentários/Anexos não têm endpoint próprio (`026-maintenance-orders.md`,
"Fora de escopo") — construir uma "Timeline Universal" agora seria, na prática, reembalar
`ordens_servico_status_history` sozinho sob um nome que promete mais fontes do que a API realmente
tem (D241 — API não promete estado que o domínio não alcança, aplicado aqui a um endpoint de
leitura, não só a comandos). Por isso este endpoint se chama e se comporta como o que realmente é: o
**Histórico Operacional** (status history puro). Quando os demais sub-recursos existirem, uma
verdadeira Timeline Universal para OS pode ser adicionada como um documento novo, sem quebrar este.

## `GET /api/v1/ordens-servico/{id}/historico-status`

**Segurança**: `bearerAuth` + `maintenance.work_order.view` — `RBAC_MATRIX.md` §7.9 não tem um
código dedicado para "ver histórico"; reaproveitado `.view` (ver histórico de status é parte de ver
a OS, mesmo raciocínio de `019-trip-timeline.md` reaproveitando `freight.trip.view`).

**Cursor pagination** — volume "Médio" hoje (`relational/005-manutencao.md`: "uma OS gera bem menos
transições que uma Viagem"), mas a natureza da tabela é Histórica/append-only, mesma regra de
`PAGINATION.md` aplicada a toda entrada em `ordens_servico_status_history`, independente do volume
atual — evita reescrever o contrato se o volume crescer.

**Query parameters**: `cursor`, `limit`, `status` (filtra por valor de status na linha).

**Responses**: `200` (coleção cursor-paginada de `MaintenanceOrderStatusHistoryEntry`,
`maintenance-schemas.md`), `401`, `403`, `404`, `500`.

## D257 — nenhum endpoint operacional reescreve o histórico

Toda linha nasce como efeito colateral de um comando em `026-maintenance-orders.md`/`028-
maintenance-approvals.md` — nunca de uma escrita direta neste caminho. Não existe `POST`/`PATCH`/
`DELETE` aqui, mesmo padrão de `024-odometer-readings.md` (D246, Lote 5) e `019-trip-timeline.md`
(D187, Lote 4).

## Como este documento cresce

Se uma Timeline Universal completa (D022) for pedida para Manutenção no futuro (juntando este
histórico com Solicitação de Peça/Comentários/Anexos), ela nasce como um documento novo (ex.:
`032-maintenance-timeline.md`), não como uma reescrita deste — este endpoint continua válido como a
fonte pura de status, a Timeline apenas o agregaria com outras fontes.
