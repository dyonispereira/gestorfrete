# 033 — Accounts Receivable (Contas a Receber)

Bounded context proprietário: `financial` (D215, D261). `contas_receber.fatura_id` é `NOT NULL` —
uma Conta a Receber **nunca existe sem uma Fatura** (D252-style Aggregate ownership). Por isso
Fatura ganha CRUD mínimo aqui (D260 — pré-requisito plenamente especificado no Domain/Dictionary/
DDL/RBAC, não pedido explicitamente na lista de arquivos do Lote 7, mas necessário para este arquivo
ser utilizável — sinalizado em "Achados do Lote 7").

## D273 — "estornar"/"cancelar" não são transições de Conta a Receber

`contas_receber_status_enum` = `PENDENTE`, `VENCIDA`, `PARCIALMENTE_RECEBIDO`, `RECEBIDA`,
`CONCILIADA` — **sem `CANCELADA`**. Correção de um valor já lançado nunca é "cancelamento" da Conta
a Receber, é Estorno (`037-bank-reconciliation.md`, `FinancialReversal`) — que aponta para a Conta
a Receber, nunca a exclui nem muda seu `status` para algo fora do enum real.

**Reconciliado (Lote Financeiro, Parte 2.1)**: `PARCIALMENTE_RECEBIDO` é valor novo — ver seção
`commands/confirm-receipt` abaixo para a mudança real de comportamento (baixa parcial passou a
funcionar de verdade; antes, `received_value` era aceito pelo schema mas ignorado pelo handler).

## `Invoice` — Fatura (D260)

### `GET /api/v1/faturas`

**Segurança**: `bearerAuth` + `financial.invoice.view`. **Query parameters**: `page`/`limit`,
`client_id` (`cliente_id`), `status`, `trip_id` (`viagem_id` — Reconciliado, Lote Financeiro Parte
3: passou a fazer `EXISTS` contra `fatura_viagens`, já que a Fatura não tem mais `viagem_id`
direto).

**Responses**: `200` (`Pagination` de `Invoice`, `financial-schemas.md`), `401`, `403`, `500`.

### `GET /api/v1/faturas/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500` — inclui `trips` (array de `InvoiceTrip`, ver
schema) quando a Fatura é por viagem(ns).

### `GET /api/v1/faturas/viagens-elegiveis` — Reconciliado (Lote Financeiro, Parte 3)

Lista as Viagens de um Cliente prontas para entrar numa Fatura — "a seleção deve mostrar somente
viagens faturáveis conforme as regras já existentes" (pedido explícito do usuário). Aplica, por
Viagem: `client_id` bate, ao menos um Canhoto registrado, CT-e emitido
(`status_fiscal ∈ {CTE_EMITIDO, MDFE_EMITIDO, MDFE_ENCERRADO}`, mesmo critério de sempre), e
**nenhuma Fatura Viagem existente em Fatura não `CANCELADA`** referenciando essa Viagem (nova
regra — antes não existia "já faturada" para checar, uma Viagem só podia aparecer numa Fatura
porque o modelo era 1:1). Lê `freight` (Viagem/Entrega/Canhoto) e a própria `fatura_viagens` —
nunca lê `documents` diretamente (D008): o `status_fiscal` da Viagem já é a projeção que
`freight`/`documents` mantêm sincronizada, financial não abre CT-e.

**Segurança**: `financial.invoice.create` (é uma consulta de apoio à criação, mesma permissão).
**Query parameters**: `client_id` (obrigatório).

**Responses**: `200` (array de `EligibleTrip`: `trip_id`, `codigo`, `data_programada`,
`suggested_value` — `Trip.receita_prevista_snapshot`, só uma sugestão inicial no formulário, nunca
o valor final sem confirmação explícita do usuário), `400` (sem `client_id`), `401`, `403`, `500`.

### `POST /api/v1/faturas`

Cria a Fatura, sua(s) Fatura Viagem (uma por Viagem selecionada) **e** a(s) Conta(s) a Receber
correspondente(s) (uma por parcela) numa única transação — atômica: falha em qualquer validação
(Viagem inelegível, cliente divergente, Viagem já faturada, duplicata na própria seleção) impede a
Fatura inteira, nenhuma Viagem fica parcialmente faturada. "Faturar" do pedido do usuário é este
endpoint, não um endpoint separado. Precondição de domínio ("Canhoto(s) registrado(s) e CT-e
emitido") é validada pela aplicação consultando `freight` — sem endpoint próprio de verificação
aqui, mesmo padrão de antes.

**Reconciliado (Lote Financeiro, Parte 3)**: `trip_id` (singular) virou `trips` (array de
`{trip_id, value}` — cada Viagem selecionada com seu valor faturável explícito, nunca inferido
silenciosamente). `total_value` deixou de ser aceito — o servidor calcula `valor_bruto` (soma de
`trips[].value`) e `valor_total = valor_bruto + adjustment_value`; aceitar um total digitado
independente das origens era exatamente o que o usuário pediu para eliminar. `delivery_id`
continua existindo, inalterado, mutuamente exclusivo com `trips` (mesma regra de sempre, agora
validada contra "`trips` não vazio" em vez de "`trip_id` presente").

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          trips:
            type: array
            minItems: 1
            items:
              type: object
              properties:
                trip_id: { $ref: "components/schemas.md#/UUID" }
                value: { type: string }
              required: [trip_id, value]
          delivery_id: { $ref: "components/schemas.md#/UUID" }
          client_id: { $ref: "components/schemas.md#/UUID" }
          adjustment_value: { type: string, default: "0" }
          adjustment_reason: { type: string, nullable: true }
          payment_method_id: { $ref: "components/schemas.md#/UUID" }
          installments:
            type: array
            items:
              type: object
              properties:
                value: { type: string }
                due_date: { type: string, format: date }
              required: [value, due_date]
        required: [client_id, payment_method_id, installments]
```

`trips` (não vazio) e `delivery_id` — exatamente um dos dois presente —
`400` (`FINANCIAL_INVOICE_ORIGIN_MISMATCH`) caso contrário.
`adjustment_reason` obrigatório quando `adjustment_value ≠ "0"` —
`400` (`FINANCIAL_INVOICE_ADJUSTMENT_REASON_REQUIRED`) caso contrário. Nenhum
`trip_id` repetido dentro do próprio array `trips` — `400` (`FINANCIAL_INVOICE_DUPLICATE_TRIP`).
Todas as Viagens de `trips` precisam ter `cliente_id` igual a `client_id` —
`409` (`FINANCIAL_INVOICE_CLIENT_MISMATCH`) caso alguma divirja. Cada Viagem precisa estar
elegível (ver `viagens-elegiveis` acima) — `409` (`FINANCIAL_INVOICE_MISSING_PRECONDITION`) quando
falta Canhoto/CT-e, `409` (`FINANCIAL_INVOICE_TRIP_ALREADY_INVOICED`) quando já há uma Fatura
Viagem ativa para essa Viagem.

**Efeito colateral documentado**: para cada Viagem em `trips`, a criação transiciona o Status
Financeiro dessa Viagem `AGUARDANDO_FATURAMENTO → FATURADA` (`018-trip-status.md`, dimensão
Financeira, já `readOnly` lá) — Financial não escreve `viagens.status_operacional` (regra do
usuário respeitada), mas **é** o dono de `status_financeiro`, dimensão distinta (D020). Acontece
depois do commit da transação principal (mesmo padrão cross-module de todo o resto do sistema — D262-style),
uma chamada por Viagem.

**Compatibilidade**: faturar uma única Viagem é `trips` com um elemento — mesmo endpoint, mesma
validação, mesmo motor (não existe mais um caminho "individual" separado).

**Segurança**: `financial.invoice.create`. **Idempotency-Key**: aceita e com enforcement real
(Reconciliado, V1 Operational Hardening Parte 6 — `core/idempotency/`, `IDEMPOTENCY.md`); a
documentação anterior dizia "obrigatório" sem nunca ter sido de fato exigida ou aplicada (D418) —
corrigido aqui para refletir o comportamento real: aceita, não exigida (não quebra clientes que
ainda não a enviam), mas real quando enviada — mesma chave + mesmo corpo nunca cria uma segunda
Fatura.

**Responses**: `201` (`Invoice`, com `trips` no corpo), `400` — `FINANCIAL_INVOICE_ORIGIN_MISMATCH`,
`FINANCIAL_INVOICE_ADJUSTMENT_REASON_REQUIRED`, `FINANCIAL_INVOICE_DUPLICATE_TRIP`, `401`, `403`,
`404` (Cliente/Forma de Pagamento/Viagem/Entrega não existe), `409` —
`FINANCIAL_INVOICE_MISSING_PRECONDITION` (canhoto/CT-e ausente), `FINANCIAL_INVOICE_CLIENT_MISMATCH`,
`FINANCIAL_INVOICE_TRIP_ALREADY_INVOICED`, `500`.

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

### `GET /api/v1/contas-receber` — Reconciliado (Lote Financeiro, Parte 2.1)

Consulta agregada entre Faturas — "o que tenho para receber hoje" sem abrir Fatura por Fatura.
Ownership não muda (Conta a Receber continua sub-recurso de Fatura, D260); é só uma superfície de
leitura própria, sem `POST`/`PATCH`/comandos aqui — a baixa continua só em
`/faturas/{id}/contas-receber/{parcelaId}/commands/confirm-receipt` acima. Gap real registrado na
Parte 2 ("CR não deveria existir operacionalmente apenas dentro de Fatura"), fechado aqui.

**Segurança**: `bearerAuth` + `financial.receivable.view`. **Query parameters**: `page`/`limit`,
`status`, `client_id` (join com `faturas.cliente_id` — não existe na tabela `contas_receber`),
`accounting_period` (`competencia`, igualdade exata), `due_date__gte`/`__lte`.

**Responses**: `200` (`Pagination` de `AccountsReceivable`, agora também com `invoice_id` e
`client_id` — os dois só preenchidos/relevantes aqui, `null` nas rotas aninhadas onde já são óbvios
pelo contexto da URL), `401`, `403`, `500`.

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

`PENDENTE`/`VENCIDA`/`PARCIALMENTE_RECEBIDO → PARCIALMENTE_RECEBIDO`/`RECEBIDA`. **Este é o
"registrar recebimento" pedido no kickoff** — não existe `POST /recebimentos` separado (D264,
mesmo padrão de `commands/pay` em `032`). Publica `RecebimentoConfirmado` (já em `EVENT_MAP.md`)
quando o saldo chega a zero, que avança o Status Financeiro da Viagem para `RECEBIDA` quando
**todas** as parcelas da Fatura estiverem 100% recebidas (nunca no meio de uma baixa parcial).

**Reconciliado (Lote Financeiro, Parte 2.1)**: `received_value` agora é lido de verdade pelo
handler (era aceito pelo schema e ignorado — gap registrado na Parte 2, fechado aqui) — é o valor
da baixa em si, não o valor total da parcela. Invariante: `0 < received_value <= saldo em aberto`
(`value - valor já recebido antes`); violar isso é `409` —
`FINANCIAL_RECEIVABLE_INVALID_PAYMENT_VALUE`. Chamável repetidamente enquanto houver saldo aberto —
cada chamada é uma baixa, não uma operação de uma vez só. Quando o saldo zera, `status → RECEBIDA`;
antes disso, `status → PARCIALMENTE_RECEBIDO`.

**Segurança**: `financial.receivable.confirm_receipt`. **Idempotency-Key**: aceita e com
enforcement real (Reconciliado, V1 Operational Hardening Parte 6 — corrige a mesma lacuna
documentada acima em `POST /faturas`: "obrigatório" nunca foi de fato aplicado antes desta rodada).

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

**Responses**: `200` (`AccountsReceivable`), `400`, `401`, `403`, `404`, `409` —
`FINANCIAL_RECEIVABLE_INVALID_TRANSITION` (parcela já `RECEBIDA`/`CONCILIADA`),
`FINANCIAL_RECEIVABLE_INVALID_PAYMENT_VALUE` (valor fora de `0 < x <= saldo em aberto`), `500`.

### `RECEBIDA → CONCILIADA` — externa, fora de escopo deste endpoint

Via `037-bank-reconciliation.md`, mesmo padrão de `032`.

### Sem `DELETE`

`RBAC_MATRIX.md` não tem `financial.receivable.delete` — correção via Estorno (D266), nunca soft
delete (diferente de Contas a Pagar, que ainda está em fase de lançamento quando `LANCADA`; Conta a
Receber só existe quando a Fatura já foi emitida, um estágio mais avançado e mais sensível a
remoção silenciosa).

## `PaymentMethod` — Forma de Pagamento (D386, Reconciliado — Lote Financeiro, Parte 2.1)

`faturas.forma_pagamento_id` é FK `NOT NULL` desde `032`/`033` — a entidade/Repository já
existiam, mas sem contrato de API/RBAC próprio; a UI usava um campo de ID cru até aqui, mesmo
padrão temporário de `VehicleCategory` (D363). Cadastro mestre mínimo (`nome`+`status`, sem
`codigo`/`audit`).

### `GET /api/v1/formas-pagamento`

**Segurança**: `financial.payment_method.view`. **Query parameters**: `page`/`limit`, `status`.

**Responses**: `200` (`Pagination` de `PaymentMethod`), `401`, `403`, `500`.

### `GET /api/v1/formas-pagamento/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### `POST /api/v1/formas-pagamento`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
        required: [nome]
```

**Segurança**: `financial.payment_method.create`. **Responses**: `201` (`PaymentMethod`), `400`,
`401`, `403`, `409` — `FINANCIAL_PAYMENT_METHOD_NAME_ALREADY_EXISTS`
(`uq_formas_pagamento_tenant_id_nome`), `500`.

### `PATCH /api/v1/formas-pagamento/{id}`

`nome`/`status` (`ATIVA`/`INATIVA`) — `status: INATIVA` é a forma real de desativar, sem `DELETE`
(mesmo padrão de `CostCenter`/`ChartOfAccounts`, cadastro mestre referenciado por FK).

**Segurança**: `financial.payment_method.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`,
`500`.

## Fora de escopo, não esquecido

- **Ocorrência financeira** (divergência de conciliação, inadimplência): citada em `005-
  FINANCEIRO.md`, sem endpoint dedicado neste lote — mesmo padrão de `Ocorrência` de Viagem (Lote
  4), que já existe; uma futura "Ocorrência Financeira" pode reutilizar o mesmo desenho.
- **Reemissão fiscal após `commands/cancel`**: pertence a `009-FISCAL.md` (próximo lote).

## Como este documento cresce

Se o produto precisar de faturamento parcial/split além de "uma parcela por vez", este documento
ganha uma seção específica — hoje `installments` no `POST /faturas` já cobre o caso comum
(múltiplas parcelas na criação).
