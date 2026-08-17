# 027 — Maintenance Order Items (Itens de OS)

Bounded context proprietário: `maintenance` (D215). Sub-recurso de Ordem de Serviço — Item de OS
**nunca existe fora de uma OS** (D252, garantido fisicamente por `ordem_servico_id UUID NOT NULL`
em `itens_ordem_servico`) — por isso não há `POST /itens` global, só sob o path da OS (D225).

## `GET /api/v1/ordens-servico/{id}/itens`

**Segurança**: `bearerAuth` + `maintenance.work_order_item.view`.

**Query parameters**: `page`/`limit`, `cost_category` (`categoria_custo`).

**Responses**: `200` (`Pagination` de `MaintenanceOrderItem`, `maintenance-schemas.md`), `401`,
`403`, `404` (OS não existe), `500`.

## `POST /api/v1/ordens-servico/{id}/itens`

Criar um Item recalcula `predicted_cost`/`actual_cost` da OS pai (D254) e pode disparar a transição
automática `EM_DIAGNOSTICO → AGUARDANDO_APROVACAO` (`026-maintenance-orders.md`) quando o novo total
ultrapassa a alçada configurada.

**Segurança**: `maintenance.work_order_item.create`. **Idempotency-Key**: recomendado quando o
Item representa uma categoria de custo crítica (`PECAS`/`SERVICOS`/`TERCEIROS`) — evita duplicar
lançamento por retry de rede.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          cost_category: { type: string, enum: [PECAS, PNEUS, SERVICOS, TERCEIROS, MAO_DE_OBRA_INTERNA, MAO_DE_OBRA_TERCEIRIZADA, DESLOCAMENTO, OUTROS] }
          description: { type: string }
          stock_part_id: { $ref: "components/schemas.md#/UUID" }
          quantity: { type: string }
          unit_value: { type: string }
        required: [cost_category, description, quantity, unit_value]
```

`stock_part_id` só é aceito quando `cost_category = PECAS` — `400` caso contrário
(`MAINTENANCE_ITEM_STOCK_PART_INVALID_CATEGORY`).

**Responses**: `201` (`MaintenanceOrderItem`), `400`, `401`, `403`, `404` (OS ou Peça em Estoque não
existe), `409` — `MAINTENANCE_ORDER_ITEM_INVALID_STATUS` (OS já `FECHADA`/`CANCELADA` — itens não
podem ser adicionados a uma OS encerrada), `500`.

## `PATCH /api/v1/ordens-servico/{id}/itens/{itemId}`

D229 — parcial (`description`, `quantity`, `unit_value`, `stock_part_id`). `total_value` nunca é
aceito no corpo (`GENERATED`, D254) — reflete automaticamente a nova `quantity × unit_value`.

**Segurança**: `maintenance.work_order_item.edit`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_ITEM_INVALID_STATUS`,
`500`.

## Sem `DELETE`

`RBAC_MATRIX.md` §7.9 não tem `maintenance.work_order_item.delete`/`.cancel` — coerente com o
princípio geral do sistema de nunca apagar uma linha de custo já lançada (mesmo espírito de D001
aplicado a Item de OS); um lançamento incorreto é corrigido via `PATCH`, nunca removido.

## D087 — Item de OS nunca representa saldo/estoque

`quantity`/`unit_value`/`total_value` aqui descrevem **consumo dentro desta OS**, nunca o saldo do
Almoxarifame. `stock_part_id` é uma referência de leitura (Peça em Estoque não tem endpoint próprio
neste lote, `026-maintenance-orders.md` seção "Fora de escopo") — a baixa de estoque em si
(`movimentacoes_estoque`) acontece em outro sub-sistema, fora do escopo desta API.

## Como este documento cresce

Quando Peça em Estoque/Movimentação de Estoque ganharem endpoint próprio, `stock_part_id` passa a
ser consultável — nenhuma mudança de schema necessária aqui, só a adição do novo endpoint em outro
lote.
