# 088 — Webhooks

Bounded context proprietário: `integration` (D215). `webhooks` — Master Data, D111/D138: entrega
idempotente, reprocessável sem efeito colateral.

## `GET /api/v1/integrations/webhooks`

**Segurança**: `bearerAuth` + `integration.webhook.view`.

**Query parameters**: `page`/`limit`, `integration_config_id`, `status`
(`ATIVO`/`INATIVO`/`SUSPENSO`).

**Responses**: `200` (`Pagination` de `Webhook`, `components/transversal-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/integrations/webhooks/{id}`

**Responses**: `200` (`Webhook`), `401`, `403`, `404`, `500`.

## `POST /api/v1/integrations/webhooks`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          integration_config_id: { $ref: "components/schemas.md#/UUID", description: "Opcional — um webhook pode ser standalone (domain: 'sem uma integração completa por trás')." }
          target_url: { type: string, format: uri }
          subscribed_events: { type: array, items: { type: string }, minItems: 1, description: "Nomes de eventos de EVENT_MAP.md — nunca validados contra uma lista fechada aqui, o catálogo é a fonte da verdade." }
        required: [target_url, subscribed_events]
```

`segredo_hmac_arquivo_id` **nunca é aceito no corpo** — gerado pelo backend na criação (mesmo
princípio de `TOKEN_API.TOKEN_HASH`, D084) e devolvido **uma única vez** na resposta deste `POST`
(nunca novamente em nenhum `GET` subsequente — mesma disciplina de segredo exibido uma vez só já
aplicada a credenciais de API em outros sistemas deste porte).

**Segurança**: `integration.webhook.create`.

**Responses**: `201` (`Webhook` + `signing_secret` presente só nesta resposta), `400`, `401`, `403`,
`404` (`integration_config_id` informado mas não existe), `500`.

## `PATCH /api/v1/integrations/webhooks/{id}`

D229 — parcial (`target_url`, `subscribed_events`). Nunca reemite `signing_secret` — regenerar o
segredo é um comando explícito (ver abaixo), não um efeito colateral de editar a URL.

**Segurança**: `integration.webhook.edit`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## `POST /api/v1/integrations/webhooks/{id}/commands/activate`

`INATIVO`/`SUSPENSO → ATIVO`.

**Segurança**: `integration.webhook.activate`.

**Responses**: `200` (`Webhook`), `401`, `403`, `404`, `409`, `500`.

## `POST /api/v1/integrations/webhooks/{id}/commands/suspend`

Qualquer estado `→ SUSPENSO` (manual — `SUSPENSO` automático por falhas consecutivas é resultado de
processamento interno, não deste comando).

**Segurança**: `integration.webhook.suspend`.

**Responses**: `200`, `401`, `403`, `404`, `409`, `500`.

## `POST /api/v1/integrations/webhooks/{id}/commands/test`

Envia um payload de teste (evento sintético, nunca um evento de domínio real) ao `target_url`,
assinado com o mesmo segredo HMAC — permite ao Tenant validar o endpoint de destino antes de
assinar eventos reais.

**Segurança**: `integration.webhook.test`. **Idempotency-Key**: não aplicável (efeito é só a
chamada HTTP externa, não um estado persistido).

**Responses**: `200` (`{delivered: boolean, http_status, duration_ms}` — resultado imediato da
tentativa síncrona de teste), `401`, `403`, `404`, `500`.

## Histórico de tentativas de entrega — lacuna documentada, não inventada

**`webhooks` não tem tabela de tentativas de entrega** — nenhuma coluna ou tabela física registra
histórico de chamadas HTTP individuais (só o estado atual, `status`). `WebhookEntregue`/
`WebhookFalhou` existem como eventos (D327, `EVENT_MAP.md`, consumidos por `analytics`/`audit`),
mas **não há endpoint aqui para consultar esse histórico diretamente** — pedido explícito do
usuário para manter isso claro: "histórico de tentativas de entrega ainda é uma lacuna documentada,
não uma entidade inventada". Nenhuma tabela `webhook_deliveries` foi criada para preencher esta
lacuna; fica para quando o produto pedir explicitamente, com sua própria auditoria de volume/
retenção (mesma disciplina de `031-maintenance-triggers.md`/`056-driver-checklists.md`).

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `integration.webhook.delete` — desativação via `commands/suspend`.

## Como este documento cresce

Regenerar `signing_secret` (rotação de segurança) é um comando aditivo natural
(`commands/rotate-secret`) quando o produto pedir — não inventado aqui por não ter sido pedido
explicitamente nem ter RBAC próprio ainda.
