# 035 — Recurring Billing (Assinatura, Plano, Cobrança Recorrente)

## D272 — Bounded context real: `subscription`/`billing`, não `financial`

Este arquivo está numerado dentro do Lote 7 por agrupamento temático do pedido do usuário
("Financeiro"), mas **`Assinatura`/`Plano`/`Cobrança Recorrente` não pertencem ao bounded context
`financial`** (D261 — que é o dinheiro do tenant com os próprios clientes/fornecedores). São o
billing do próprio GestorFrete cobrando a transportadora-tenant, fisicamente em
[`../database/relational/001-core.md`](../database/relational/001-core.md), com RBAC em
`RBAC_MATRIX.md` §7.19 `subscription`/`billing` — confirmado por leitura completa, não assumido. As
tags OpenAPI deste arquivo são `Subscriptions`/`RecurringBilling`, nunca `Financial*` (D215 aplicado
com rigor mesmo quando o agrupamento do lote sugere o contrário).

## D272-nota — enum físico é mais restrito que a máquina conceitual

`flows/001-ONBOARDING.md` documenta uma máquina de 8 estados para "Tenant / Assinatura"
(`RASCUNHO`/`AGUARDANDO_PAGAMENTO`/`TRIAL`/`ATIVO`/`INADIMPLENTE`/`SUSPENSO`/
`CANCELAMENTO_SOLICITADO`/`CANCELADO`) — mas `assinaturas_status_enum` real
(`relational/001-core.md`) só tem **4 valores**: `TRIAL`, `ATIVA`, `CANCELADA`, `SUSPENSA`. Os
quatro estados intermediários (`RASCUNHO`, `AGUARDANDO_PAGAMENTO`, `INADIMPLENTE`,
`CANCELAMENTO_SOLICITADO`) existem na máquina conceitual do fluxo de Onboarding mas nunca foram
materializados no Enum físico de `assinaturas`. Por D241 (API não promete estado que o domínio não
alcança), este contrato expõe **só as transições que o Enum físico suporta** — os quatro estados
extras ficam documentados como lacuna conhecida (D242), não inventados, não simulados por um valor
aproximado.

## D269 — `assinaturas_status_history` (gap corrigido nesta preparação)

Antes desta preparação, `assinaturas.status` não tinha tabela de histórico (D017/D018) — corrigida
em `relational/001-core.md` (ver `DECISIONS.md` D269). `TenantStatusHistory` (`tenants.status`,
citada no mesmo fluxo) é uma tabela relacionada mas diferente, ainda sem `CREATE TABLE` — gap
identificado, não corrigido aqui (fora do escopo deste lote de API).

## `SubscriptionPlan` — Plano (somente leitura)

### `GET /api/v1/planos`

Planos são definidos pela operadora da plataforma (GestorFrete), não pelo tenant — mesmo padrão de
`/permissions` (Lote 2, Platform Reference Data).

**Segurança**: `bearerAuth` + `subscription.plan.view`. **Query parameters**: `page`/`limit`,
`status`.

**Responses**: `200` (`Pagination` de `SubscriptionPlan`, `financial-schemas.md`), `401`, `403`,
`500`.

### `GET /api/v1/planos/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### Sem `POST`/`PATCH`/`DELETE`

`RBAC_MATRIX.md` §7.19 só tem `.plan.view` — gestão de Plano é administração da própria plataforma
GestorFrete (mesmo padrão de `/permissions`, Lote 2, `RBAC_MATRIX.md` §7.26), fora da superfície do
produto.

## `Subscription` — Assinatura

### `GET /api/v1/assinatura`

Singular, não `/assinaturas` — no contexto autenticado, existe no máximo uma Assinatura `ATIVA` por
tenant (`uq_assinaturas_tenant_id_status_ativa`); o tenant nunca lista "assinaturas de outros
tenants" (D208, tenant sempre do contexto). Retorna a assinatura vigente (`ATIVA`/`TRIAL`/
`SUSPENSA`) ou a mais recente `CANCELADA`.

**Segurança**: `subscription.subscription.view`. **Responses**: `200` (`Subscription`), `401`,
`403`, `404` — `SUBSCRIPTION_NOT_FOUND` (tenant sem nenhuma Assinatura, cenário só possível durante
onboarding em andamento), `500`.

### Sem `POST`

Assinatura nasce do fluxo de Onboarding (`flows/001-ONBOARDING.md`), nunca de um `POST` genérico
neste endpoint — `RBAC_MATRIX.md` §7.19 não tem `.subscription.create`, coerente com essa origem.

### `POST /api/v1/assinatura/commands/upgrade`

Troca `plano_id` para um plano de tier superior. Se a assinatura estiver em `TRIAL`, o upgrade
também transiciona `TRIAL → ATIVA` (conversão trial-para-pago, a única forma de sair de `TRIAL` sem
esperar expiração).

**Segurança**: `subscription.subscription.upgrade`. **Idempotency-Key**: obrigatório (D211).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          plan_id: { $ref: "components/schemas.md#/UUID" }
        required: [plan_id]
```

**Responses**: `200` (`Subscription`), `400`, `401`, `403`, `404` (`plan_id` não existe), `409` —
`SUBSCRIPTION_UPGRADE_INVALID_STATUS` (ex: a partir de `CANCELADA`), `500`.

### `POST /api/v1/assinatura/commands/downgrade`

Mesma mecânica, plano de tier inferior — não transiciona `status` (só faz sentido a partir de
`ATIVA`).

**Segurança**: `subscription.subscription.downgrade`. **Idempotency-Key**: obrigatório.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` — `SUBSCRIPTION_DOWNGRADE_INVALID_STATUS`,
`500`.

### `POST /api/v1/assinatura/commands/cancel`

`ATIVA`/`TRIAL → CANCELADA`. Exige confirmação explícita (D010).

**Segurança**: `subscription.subscription.cancel` — RBAC marca "Aprovação: Administrador Empresa"
(criticidade Alta), reforçando no Backend que só o Usuário Master/Administrador do tenant pode
executar, não qualquer usuário com a permissão técnica.

**Idempotency-Key**: obrigatório.

**Responses**: `200` (`Subscription`), `401`, `403`, `404`, `409` —
`SUBSCRIPTION_CANCEL_INVALID_STATUS` (ex: já `CANCELADA`, ou `SUSPENSA` — mesma restrição normativa
de `003-MANUTENCAO.md`: cancelamento voluntário só a partir de estados "saudáveis"), `500`.

### `POST /api/v1/assinatura/commands/reactivate`

`CANCELADA`/`SUSPENSA → ATIVA`.

**Segurança**: `subscription.subscription.reactivate`. **Idempotency-Key**: obrigatório.

**Responses**: `200`, `401`, `403`, `404`, `409` — `SUBSCRIPTION_REACTIVATE_INVALID_STATUS`, `500`.

### `TRIAL → SUSPENSA` — Derivada, fora de escopo de comando

"Trial expira sem conversão" é automático (job periódico comparando `data_fim_trial` contra a data
atual) — sem comando de API, mesmo padrão de `PENDENTE → VENCIDA` em `033-accounts-receivable.md`.

## `RecurringCharge` — Cobrança Recorrente

### `GET /api/v1/cobrancas-recorrentes`

**Segurança**: `billing.recurring_charge.view`. **Query parameters**: `page`/`limit`, `status`,
`due_date__gte`/`__lte`.

**Responses**: `200` (`Pagination` de `RecurringCharge`, `financial-schemas.md`), `401`, `403`,
`500`.

### `GET /api/v1/cobrancas-recorrentes/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### Sem `POST`/`PATCH`/`DELETE`

Cobrança nasce automaticamente a cada ciclo de faturamento da Assinatura (job periódico) — nenhuma
criação/edição/exclusão manual modelada no domínio, sem RBAC para isso.

### `POST /api/v1/cobrancas-recorrentes/{id}/commands/retry`

`FALHOU → PENDENTE` (nova tentativa enfileirada) — o resultado definitivo (`PAGA`/`FALHOU`
novamente) chega depois, de forma assíncrona, via consumidor interno do webhook do provedor (D265 —
a API de negócio não expõe detalhes do provedor; o webhook do Asaas nunca é um endpoint desta
API, é tratado por um módulo de integração à parte).

**Segurança**: `billing.recurring_charge.retry`. **Idempotency-Key**: obrigatório (D211 — evita
disparar duas tentativas de cobrança para a mesma falha).

**Responses**: `200` (`RecurringCharge`), `401`, `403`, `404`, `409` —
`BILLING_RECURRING_CHARGE_INVALID_STATUS` (só válido a partir de `FALHOU`), `500`.

## D265 — Asaas nunca aparece neste contrato

Nenhum campo de referência de transação Asaas (`asaas_payment_id` ou similar) está exposto aqui —
`relational/001-core.md` já registra essa integração como "campo de infraestrutura... a confirmar em
`011-administracao.md`, não decidido aqui". Quando o módulo de Integração for modelado, ele consome
`RecurringCharge`/`Subscription` por dentro (nunca o cliente HTTP falando diretamente com Asaas
através desta API).

## Fora de escopo, não esquecido

- Os quatro estados conceituais sem Enum físico (`RASCUNHO`/`AGUARDANDO_PAGAMENTO`/
  `INADIMPLENTE`/`CANCELAMENTO_SOLICITADO`) — ver D272-nota.
- `TenantStatusHistory`/`tenants.status` — gap relacionado, não corrigido neste lote.
- Webhook Asaas e qualquer detalhe do provedor de pagamento — módulo de Integração futuro.

## Como este documento cresce

Se `assinaturas_status_enum`/`tenants_status_enum` forem expandidos para cobrir a máquina completa
de `flows/001-ONBOARDING.md` (decisão de Core/Tenancy, não deste lote), este documento ganha os
comandos correspondentes (`commands/regularize`, transições de `INADIMPLENTE`, etc.) — a estrutura
de comandos já usada aqui (`upgrade`/`downgrade`/`cancel`/`reactivate`) se estende sem quebrar o
contrato existente.
