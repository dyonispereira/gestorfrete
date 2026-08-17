# 015 — Trip Deliveries

Bounded context proprietário: `freight` (D215). Entrega (D232 — sub-recurso, ciclo de vida
controlado por Viagem) e Canhoto (sub-recurso de Entrega, mesmo raciocínio).

## Por que não existe `POST /api/v1/entregas`

Entrega **pertence** à Viagem (`entregas.viagem_id NOT NULL`, `uq_entregas_viagem_id_ordem`) — não
tem sentido de negócio fora dela (D232/D225). Criar um endpoint de topo permitiria montar uma
Entrega órfã ou associá-la à Viagem errada por engano no corpo da requisição — o mesmo raciocínio
já aplicado a Endereço (`011-addresses.md`) e a Contato (`012-contacts.md`).

```
GET/POST         /api/v1/viagens/{id}/entregas
GET/PATCH        /api/v1/viagens/{id}/entregas/{entregaId}
POST             /api/v1/viagens/{id}/entregas/{entregaId}/canhoto
```

**Sem `DELETE`** — RBAC (`freight.delivery.*`) não tem código de exclusão (confirmado por leitura
de `RBAC_MATRIX.md` 7.13: só `.view`/`.create`/`.edit`); uma Entrega errada é corrigida via
`status: CANCELADA`, nunca removida (histórico de tentativa de entrega é auditável, D001/D007).

## `GET /api/v1/viagens/{id}/entregas`

**Segurança**: `bearerAuth` + `freight.delivery.view`.

**Responses**: `200` (`Pagination` de `Delivery`, `trip-schemas.md`), `401`, `403`, `404` (Viagem
não existe), `500`.

## `GET /api/v1/viagens/{id}/entregas/{entregaId}`

**Segurança**: `freight.delivery.view`. **Responses**: `200` (`Delivery`), `401`, `403`, `404`,
`500`.

## `POST /api/v1/viagens/{id}/entregas`

**Segurança**: `freight.delivery.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          order: { type: integer, minimum: 1 }
          recipient: { type: string }
          delivery_address:
            type: object
            description: Passthrough — mesmo formato de `endereco_entrega` (JSONB).
          window:
            type: object
            nullable: true
            properties:
              starts_at: { type: string, format: date-time }
              ends_at: { type: string, format: date-time }
            required: [starts_at, ends_at]
        required: [order, recipient, delivery_address]
```

**`order` duplicado na mesma Viagem é rejeitado** — reflete `uq_entregas_viagem_id_ordem`
diretamente:

**Responses**

| Código | Corpo |
|---|---|
| `201` | `Delivery` criada |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — Viagem não existe |
| `409` | `Conflict` (D230) — `FREIGHT_DELIVERY_ORDER_ALREADY_EXISTS` (`uq_entregas_viagem_id_ordem`) — a API rejeita antes mesmo de chegar ao banco quando possível, mas a constraint física é a garantia final |
| `422` | `UnprocessableEntity` — `window.ends_at` ≤ `window.starts_at` (`ck_janelas_entrega_hora_fim_apos_inicio`) |
| `500` | `InternalServerError` |

## `PATCH /api/v1/viagens/{id}/entregas/{entregaId}`

**Segurança**: `freight.delivery.edit`. D229 — parcial.

`status` **pode** ser alterado aqui (diferente de Viagem, D233) — Entrega não tem uma máquina de
estados tão rica quanto Viagem, e sua transição não dispara os mesmos efeitos colaterais de
domínio complexos que justificariam um comando próprio; ainda assim, `status: RECUSADA` exige
`rejection_reason` preenchido (validação de aplicação, espelha `motivo_recusa`).

**Efeito colateral documentado (D237 — Aggregate Root controla)**: quando a última Entrega
`PENDENTE` de uma Viagem atinge um estado terminal (`CONCLUIDA`/`RECUSADA`/`DEVOLVIDA`/
`CANCELADA`), a Viagem avança automaticamente `EM_ENTREGA → FINALIZADA` (sujeito às demais
pré-condições — canhotos registrados, `018-trip-status.md`) — este `PATCH` nunca altera
`Trip.status` diretamente, mas pode disparar a transição como consequência, através do Domain, não
do Controller (D214).

**Responses**: `200` (`Delivery`), `400`, `401`, `403`, `404`, `422` — `FREIGHT_DELIVERY_
REJECTION_REASON_REQUIRED`, `500`.

## `POST /api/v1/viagens/{id}/entregas/{entregaId}/canhoto`

Registra o Canhoto de uma Entrega (1:1, `uq_canhotos_entrega_id`). **`Idempotency-Key`
obrigatória** (seção 15 do pedido — "registrar canhoto" está na lista explícita de comandos
críticos).

**Segurança**: `freight.pod.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          signature_file_id:
            $ref: "components/schemas.md#/UUID"
            description: Referência ao Storage (D107) — o binário da assinatura já foi enviado
              separadamente via o fluxo de upload padrão, nunca dentro deste corpo JSON.
```

**Fotos adicionais do canhoto físico** (múltiplas por Entrega) usam o sistema compartilhado de
Anexos, nunca este endpoint — `POST` equivalente a `entidade_tipo=CANHOTO`/`entidade_id=<id do
Canhoto>` no endpoint de Anexos (fora do escopo deste lote — Anexos/Comentários, sistema
compartilhado D186, ainda não tem seu próprio contrato de API; nota registrada, não inventada
aqui). `freight.pod.attach` (RBAC) é a permissão reservada para quando esse endpoint existir.

**Efeito colateral documentado**: `CanhotoRegistrado` (evento, `EVENT_MAP.md`) dispara gatilho de
faturamento em `financial` (Status Financeiro `AGUARDANDO_FATURAMENTO → FATURADA`, quando também
houver CT-e emitido) — fora do controle direto deste endpoint, consumido assincronamente.

**Responses**: `201` (`ProofOfDelivery`), `400`, `401`, `403`, `404`, `409` (D211/D230 —
Idempotency-Key reusada, ou Canhoto já registrado para esta Entrega, `uq_canhotos_entrega_id`),
`500`.

## Fora de escopo deste lote (não esquecido)

- **Coleta** (`coletas`) e **Romaneio**/**Item de Carga** (`romaneios`/`itens_carga`) — tabelas
  físicas existentes, sem endpoint próprio ainda. São o gatilho real de duas transições de Status
  Operacional (`EM_DESLOCAMENTO → CARREGANDO`, `CARREGANDO → EM_TRANSITO`, ver
  [`018-trip-status.md`](./018-trip-status.md)) — até esses endpoints existirem, essas duas
  transições não são alcançáveis via API, só documentadas na máquina de estados.

## Como este documento cresce

Endpoints de Coleta/Romaneio entram num lote futuro, mesmo padrão de sub-recurso de Viagem já
estabelecido aqui.
