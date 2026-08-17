# 086 — Notifications (Notificações)

Bounded context proprietário: `notification_center` (D215). `notificacoes`/`preferencias_notificacao`
— D323: entidades criadas nesta preparação (RBAC já as antecipava, Domain/DDL nunca as tinha).

## D320 — Notificação nunca é o evento de domínio

```
ViagemAtrasada (evento, publicado por freight)
        ↓
notification_center consome o evento (D032 — freight não sabe quem consome)
        ↓
Notificação criada (canal: PUSH, evento_origem_tipo: "ViagemAtrasada")
        ↓
Entrega efetiva ao canal (push/e-mail/in-app) — mecanismo de envio, infraestrutura, fora deste contrato
```

O evento de negócio (`ViagemAtrasada`) continua pertencendo a `freight` — Notificação é sempre um
efeito colateral de entrega, nunca a origem de uma nova decisão de negócio. Este endpoint nunca
recebe um `POST` criando uma Notificação diretamente do cliente HTTP: toda Notificação nasce do
processamento interno de eventos, mesmo padrão de `Inferência de IA`/`Evento Fiscal`.

## `GET /api/v1/notifications`

Lista as notificações do próprio usuário autenticado.

**Segurança**: `bearerAuth` + `notification_center.alert.view` (App ●).

**Query parameters**: `page`/`limit`, `channel` (`IN_APP`/`PUSH`/`EMAIL`), `status`
(`NAO_LIDA`/`LIDA`).

**Responses**: `200` (`Pagination` de `Notification`, `components/transversal-schemas.md`), `401`,
`403`, `500`.

## `GET /api/v1/notifications/{id}`

**Segurança**: `notification_center.alert.view` — `403` se `usuario_destinatario_id` diferir do
usuário autenticado (notificação é sempre pessoal, nunca consultável de outro usuário mesmo por
Gestor, ao contrário de Comentário/Anexo).

**Responses**: `200` (`Notification`), `401`, `403`, `404`, `500`.

## `POST /api/v1/notifications/{id}/commands/mark-read`

`NAO_LIDA → LIDA` — única transição do domínio (`notificacoes_status_enum` tem só dois valores);
"marcar como lida" e "descartar" (linguagem do RBAC) são a mesma transição física, não dois
comandos distintos.

**Segurança**: `notification_center.alert.manage_own` (App ●) — só o próprio destinatário.

**Responses**: `200` (`Notification`, `status = LIDA`, `read_at` preenchido), `401`, `403`, `404`,
`409` — `NOTIFICATION_ALREADY_READ`, `500`.

## `GET /api/v1/notifications/channel-preferences`

Retorna a preferência do usuário para os três canais — sempre os três presentes na resposta
(default `enabled: true` quando nenhuma preferência foi salva ainda, refletindo
`preferencias_notificacao` ausente = padrão habilitado).

**Segurança**: `notification_center.channel_preference.view` (App ●).

**Responses**: `200` (array de `ChannelPreference`), `401`, `403`, `500`.

## `PATCH /api/v1/notifications/channel-preferences/{channel}`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          enabled: { type: boolean }
        required: [enabled]
```

**Segurança**: `notification_center.channel_preference.edit` (App ●) — sempre a própria preferência,
nunca a de outro usuário (sem parâmetro de usuário no path, resolvido da sessão).

**Responses**: `200` (`ChannelPreference`), `400`, `401`, `403`, `500`.

## Sem `DELETE`

Notificação não é excluída pelo usuário — permanece como histórico pessoal (`LIDA` é o estado
terminal). Se o produto pedir expurgo por retenção, isso é política de infraestrutura
(`information-model/007-DATA_RETENTION.md`), não um endpoint.

## Como este documento cresce

Se um novo canal for necessário (ex.: SMS, WhatsApp), `notificacoes_canal_enum`/
`preferencias_notificacao` ganham o valor primeiro (Domain/DDL, D101) — este contrato só reflete o
valor novo depois de existir fisicamente.
