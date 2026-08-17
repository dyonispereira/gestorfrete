# 033 — Accounts Receivable (Contas a Receber)

Bounded context proprietário: `financial` (D215, D261). `contas_receber.fatura_id` é `NOT NULL` —
uma Conta a Receber **nunca existe sem uma Fatura** (D252-style Aggregate ownership). Por isso
Fatura ganha CRUD mínimo aqui (D260 — pré-requisito plenamente especificado no Domain/Dictionary/
DDL/RBAC, não pedido explicitamente na lista de arquivos do Lote 7, mas necessário para este arquivo
ser utilizável — sinalizado em "Achados do Lote 7").

## D273 — "estornar"/"cancelar" não são transições de Conta a Receber

`contas_receber_status_enum` = `PENDENTE`, `VENCIDA`, `RECEBIDA`, `CONCILIADA` — **sem
`CANCELADA`**. Correção de um valor já lançado nunca é "cancelamento" da Conta a Receber, é Estorno
(`037-bank-reconciliation.md`, `FinancialReversal`) — que aponta para a Conta a Receber, nunca a
exclui nem muda seu `status` para algo fora do enum real.

## `Invoice` — Fatura (D260)

### `GET /api/v1/faturas`

**Segurança**: `bearerAuth` + `financial.invoice.view`. **Query parameters**: `page`/`limit`,
`client_id` (`cliente_id`), `status`, `trip_id` (`viagem_id`).

**Responses**: `200` (`Pagination` de `Invoice`, `financial-schemas.md`), `401`, `403`, `500`.

### `GET /api/v1/faturas/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### `POST /api/v1/faturas`

Cria a Fatura **e** a(s) Conta(s) a Receber correspondente(s) (uma por parcela) numa única
transação — "faturar" do pedido do usuário é este endpoint, não um endpoint separado. Precondição
de domínio ("Canhoto(s) registrado(s) e CT-e emitido", `005-FINANCEIRO.md`) é validada pela
aplicação consultando `documents` (`CanhotoRegistrado`/`CTeEmitido`) — sem endpoint próprio de
verificação aqui, evento consumido internamente.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          trip_id: { $ref: "components/schemas.md#/UUID" }
          delivery_id: { $ref: "components/schemas.md#/UUID" }
          client_id: { $ref: "components/schemas.md#/UUID" }
          total_value: { type: string }
          payment_method_id: { $ref: "components/schemas.md#/UUID" }
          installments:
            type: array
            items:
              type: object
              properties:
                value: { type: string }
                due_date: { type: string, format: date }
              required: [value, due_date]
        required: [client_id, total_value, payment_method_id, installments]
```

`trip_id`/`delivery_id` — exatamente um dos dois (`ck_faturas_origem`) — `400` caso contrário.
**Efeito colateral documentado**: quando `trip_id` está presente, cria a Fatura transiciona o
Status Financeiro da Viagem `AGUARDANDO_FATURAMENTO → FATURADA` (`018-trip-status.md`, dimensão
Financeira, já `readOnly` lá) — Financial não escreve `viagens.status_operacional` (regra do
usuário respeitada), mas **é** o dono de `status_financeiro`, dimensão distinta (D020).

**Segurança**: `financial.invoice.create`. **Idempotency-Key**: obrigatório (D211).

**Responses**: `201` (`Invoice`), `400`, `401`, `403`, `404` (Cliente/Forma de Pagamento/Viagem/
Entrega não existe), `409` — `FINANCIAL_INVOICE_MISSING_PRECONDITION` (canhoto/CT-e ausente), `500`.

### `commands/cancel`

`EMITIDA → CANCELADA` — único comando real de Fatura (D273-nota: aqui "cancelar" **existe** de
fato, `faturas_status_enum` tem `CANCELADA`). Reabre a necessidade de reemissão fiscal
(`009-FISCAL.md`, lote futuro) — fora de escopo detalhar a reemissão aqui.

**Segurança**: `financial.invoice.cancel`. **Idempotency-Key**: obrigatório.

**Responses**: `200` (`Invoice`), `401`, `403`, `404`, `409` — `FINANCIAL_INVOICE_INVALID_STATUS`,
`500`.

### Sem `PATCH`/`DELETE`

`valor_total` é imutável após emitida (D100) — correção via `037`'s `FinancialReversal`, nunca
`PATCH`. Sem `.edit` em `RBAC_MATRIX.md` §7.18 para Fatura, coerente com essa imutabilidade (não é
uma lacuna, é o desenho pretendido, mesmo raciocínio de `023-vehicle-compositions.md`/D248).

## `AccountsReceivable` — Conta a Receber

### `GET /api/v1/faturas/{id}/contas-receber`

**Segurança**: `financial.receivable.view`. **Responses**: `200` (`Pagination` de
`AccountsReceivable`), `401`, `403`, `404`, `500`.

### `GET /api/v1/faturas/{id}/contas-receber/{parcelaId}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### `POST /api/v1/faturas/{id}/contas-receber`

Adiciona uma parcela extra a uma Fatura já emitida (caso raro — a maioria nasce via `POST
/faturas`). **Segurança**: `financial.receivable.create`. **Idempotency-Key**: recomendado.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          value: { type: string }
          due_date: { type: string, format: date }
        required: [value, due_date]
```

**Responses**: `201` (`AccountsReceivable`), `400`, `401`, `403`, `404`, `409` — `numero_parcela`
duplicado (`uq_contas_receber_fatura_id_parcela`), `500`.

### `PATCH /api/v1/faturas/{id}/contas-receber/{parcelaId}`

D229 — parcial (`value`, `due_date`). Só em `status = PENDENTE`/`VENCIDA` — imutável após
`CONCILIADA` (D100).

**Segurança**: `financial.receivable.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409`
— `FINANCIAL_RECEIVABLE_INVALID_STATUS`, `500`.

### `PENDENTE → VENCIDA` — Derivada

Automática, sem comando — a aplicação recalcula quando `data_vencimento` passa (job periódico, não
detalhado aqui).

### `commands/confirm-receipt`

`PENDENTE`/`VENCIDA → RECEBIDA`. **Este é o "registrar recebimento" pedido no kickoff** — não existe
`POST /recebimentos` separado (D264, mesmo padrão de `commands/pay` em `032`). Publica
`RecebimentoConfirmado` (já em `EVENT_MAP.md`), que avança o Status Financeiro da Viagem para
`RECEBIDA` quando aplicável.

**Segurança**: `financial.receivable.confirm_receipt`. **Idempotency-Key**: obrigatório (D211).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          received_value: { type: string }
        required: [received_value]
```

`received_value` divergente de `value` gera `Ocorrência financeira` (mesmo texto de `005-
FINANCEIRO.md` — sem endpoint de Ocorrência Financeira detalhado neste lote, fora de escopo).

**Responses**: `200` (`AccountsReceivable`), `400`, `401`, `403`, `404`, `409` —
`FINANCIAL_RECEIVABLE_INVALID_TRANSITION`, `500`.

### `RECEBIDA → CONCILIADA` — externa, fora de escopo deste endpoint

Via `037-bank-reconciliation.md`, mesmo padrão de `032`.

### Sem `DELETE`

`RBAC_MATRIX.md` não tem `financial.receivable.delete` — correção via Estorno (D266), nunca soft
delete (diferente de Contas a Pagar, que ainda está em fase de lançamento quando `LANCADA`; Conta a
Receber só existe quando a Fatura já foi emitida, um estágio mais avançado e mais sensível a
remoção silenciosa).

## Fora de escopo, não esquecido

- **Ocorrência financeira** (divergência de conciliação, inadimplência): citada em `005-
  FINANCEIRO.md`, sem endpoint dedicado neste lote — mesmo padrão de `Ocorrência` de Viagem (Lote
  4), que já existe; uma futura "Ocorrência Financeira" pode reutilizar o mesmo desenho.
- **Reemissão fiscal após `commands/cancel`**: pertence a `009-FISCAL.md` (próximo lote).

## Como este documento cresce

Se o produto precisar de faturamento parcial/split além de "uma parcela por vez", este documento
ganha uma seção específica — hoje `installments` no `POST /faturas` já cobre o caso comum
(múltiplas parcelas na criação).
