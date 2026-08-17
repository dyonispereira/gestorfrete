# DELIVERY_IMPLEMENTATION.md — Entrega, Janela de Entrega, Canhoto

Sub-recursos de `Trip` (D232 — ciclo de vida controlado pelo agregado, nunca `POST /entregas` de
topo, `015-trip-deliveries.md`).

## `Delivery` (`entregas`)

`Delivery(BaseEntity[UUID])` — `viagem_id`, `ordem` (único por Viagem,
`uq_entregas_viagem_id_ordem` — multi-drop real, nunca `entrega1`/`entrega2`), `destinatario`,
`endereco_entrega` (JSONB passthrough), `status` (`PENDENTE`/`CONCLUIDA`/`RECUSADA`/`DEVOLVIDA`/
`CANCELADA` — **editável por `PATCH`**, diferente de `Trip.status`, D233 se aplica só à Viagem),
`data_hora_conclusao`, `motivo_recusa`.

- `CreateDeliveryHandler`: rejeita `order` duplicado (`FREIGHT_DELIVERY_ORDER_ALREADY_EXISTS`,
  409, espelha `uq_entregas_viagem_id_ordem`); cria `DeliveryWindow` opcional na mesma transação se
  `window` vier no corpo (`ck_janelas_entrega_hora_fim_apos_inicio` — `FREIGHT_DELIVERY_WINDOW_
  INVALID`, 422, se `ends_at <= starts_at`).
- `UpdateDeliveryHandler`: `status: RECUSADA` exige `rejection_reason`
  (`FREIGHT_DELIVERY_REJECTION_REASON_REQUIRED`, 422). Ao persistir uma transição para estado
  terminal, chama `Trip.on_delivery_terminal(...)` (D237 — efeito no agregado, nunca no Controller).
  Sem `DELETE` — RBAC (`freight.delivery.*`) não tem código de exclusão (confirmado em
  `RBAC_MATRIX.md` §7.13); Entrega errada é corrigida via `status: CANCELADA`.

## `DeliveryWindow` (`janelas_entrega`)

`DeliveryWindow(BaseEntity[UUID])` — 1:1 com Entrega (`uq_janelas_entrega_entrega_id`),
`hora_inicio`/`hora_fim`. Sem endpoint próprio — só criada/lida como parte do payload de
`Delivery` (`window`), nunca um sub-recurso HTTP independente.

## `ProofOfDelivery` — Canhoto (`canhotos`, D373)

`ProofOfDelivery(BaseEntity[UUID])` — 1:1 com Entrega (`uq_canhotos_entrega_id`), `status`
(`PENDENTE`/`REGISTRADO`), `data_hora_registro`, `assinatura_arquivo_id` (referência lógica ao
Storage, D107, sem FK — mesmo padrão de `documentos_veiculo.arquivo_id`, Lote 4).

`RegisterProofOfDeliveryHandler` (`POST /viagens/{id}/entregas/{entregaId}/canhoto`): cria o
Canhoto `REGISTRADO`; rejeita se já existe um para a Entrega (`FREIGHT_POD_ALREADY_REGISTERED`,
409, espelha `uq_canhotos_entrega_id`). Publica `CanhotoRegistrado` (consumido por `financial`,
fora do controle direto deste handler). Fotos adicionais usam o sistema compartilhado de Anexos —
fora do escopo deste endpoint (`entidade_tipo='CANHOTO'`, sem endpoint de Anexos ainda, D371).

## Precondição de `commands/finish`

`FinishTripHandler` consulta todas as `entregas` da Viagem: se alguma não está em estado terminal,
ou se alguma `CONCLUIDA` não tem `ProofOfDelivery.status = REGISTRADO`, levanta
`FREIGHT_TRIP_DELIVERIES_PENDING` (422 — regra de negócio, não erro de máquina de estados, D235).

## Auditoria e tenant isolation

Mesmo padrão do resto do projeto: toda criação/transição grava `logs_auditoria`;
`SqlAlchemyDeliveryRepository`/`SqlAlchemyProofOfDeliveryRepository` filtram por
`get_current_tenant_id()`.
