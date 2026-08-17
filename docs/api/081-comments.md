# 081 — Comments (Comentários)

Bounded context proprietário: `storage` (D215). `comentarios` — infraestrutura polimórfica
compartilhada (D186), mesma tabela física de `anexos` (`080`). `019-trip-timeline.md` (Lote 4)
já sinalizava esta lacuna explicitamente ("Comentários: Não — sem endpoint de API neste lote") —
fechada agora.

## Mesmo princípio de `080-attachments.md`, mesma restrição

`comentarios.entidade_tipo` é vocabulário de texto extensível, não um Enum fechado — este documento
não enumera todo dono possível, define o padrão único e ativa explicitamente `Viagem`:

```
GET/POST         /api/v1/viagens/{id}/comments
GET/PATCH/DELETE /api/v1/viagens/{id}/comments/{commentId}
```

**Nunca**: `POST /api/v1/comments` com `entity_type` livre no corpo — pedido explícito do usuário,
rejeitado por design (D316).

## Schema `Comment`

Definido em `components/transversal-schemas.md#/Comment`.

## `GET /{owner}/{id}/comments`

**Segurança**: `bearerAuth` + permissão de visualização do dono + `storage.comment.view` (App ●).

**Query parameters**: `page`/`limit`, `visible_to_client`.

**Responses**: `200` (`Pagination` de `Comment`), `401`, `403`, `404`, `500`.

## `POST /{owner}/{id}/comments`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          text: { type: string }
          visible_to_client: { type: boolean, default: false }
        required: [text]
```

`author_id` sempre capturado da sessão autenticada, nunca aceito no corpo (mesmo princípio de
D295).

**Segurança**: permissão de visualização do dono (comentar não exige poder editar a entidade, ao
contrário de Anexo — comentar é comunicação, não alteração de dado operacional) + `storage.
comment.create` (App ●).

**Responses**: `201` (`Comment`), `400`, `401`, `403`, `404`, `500`.

## `PATCH /{owner}/{id}/comments/{commentId}`

**Só o próprio autor edita** — `text`/`visible_to_client`. D229 — parcial.

**Segurança**: `storage.comment.edit_own` — o backend rejeita (`403`) quando `author_id` do
comentário difere do usuário autenticado, mesmo que ele tenha permissão de visualização do dono.

**Responses**: `200` (`Comment`), `400`, `401`, `403`, `404`, `500`.

## `DELETE /{owner}/{id}/comments/{commentId}`

**Sem soft delete próprio** (mesma disciplina de `080-attachments.md` — `comentarios` não tem
`excluido_em`/`excluido_por`, D037). **Só o próprio autor exclui**.

**Segurança**: `storage.comment.delete_own`.

**Responses**: `204`, `401`, `403`, `404`, `500`.

## `visible_to_client` — nunca um segundo canal de autorização

Este campo é **conteúdo**, consultado por uma futura superfície de Portal do Cliente (fora do
escopo desta API interna) — nunca uma permissão RBAC nem um mecanismo de autorização; um
comentário `visible_to_client = true` continua exigindo `storage.comment.view` para ser lido por
qualquer chamador desta API.

## Fora de escopo, não esquecido

Mesma nota de `080-attachments.md`: `Viagem` é o único dono ativado, demais entidades com
"Comentários suportados: Sim" seguem o padrão idêntico quando ativadas. Menções (`@usuário`, D023)
não implementadas nesta preparação — `comentarios.texto` é `TEXT` livre, sem parsing/notificação
estruturada de menção; fica para quando o produto pedir essa granularidade.

## Como este documento cresce

Novo dono segue exatamente `080-attachments.md`'s regra de crescimento.
