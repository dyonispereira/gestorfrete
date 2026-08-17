# COLLABORATION_IMPLEMENTATION.md — Attachment/Comment sobre Viagem (080/081), Busca (082), Timeline (083)

## Attachment/Comment — camada HTTP nova sobre entidade já existente

`shared/collaboration/` já tinha `Attachment`/`Comment` como Entity + Repository reais desde o Lote
5 (D371) — usados sem HTTP pelo Canhoto Mobile (Lote 9). Este lote:

1. Estende `AttachmentRepository`/`CommentRepository` (abstract, additive — mesmo padrão D408 do
   Lote 9) com os métodos que faltavam para o HTTP funcionar: `AttachmentRepository.delete`
   (hard delete real — `anexos` não tem `excluido_em`, D037/`080-attachments.md` é explícito: "sem
   soft delete próprio") e `.count_by_file_id` (para o `409 STORAGE_FILE_IN_USE` do Storage).
   `CommentRepository.update` (só `texto`/`visivel_cliente`) e `.delete` (hard delete real, mesma
   razão).
2. Cria `modules/freight/application/commands/{create,delete}_trip_attachment.py` e
   `{create,update,delete}_trip_comment.py` — Viagem é o único dono ativado (D316); comandos vivem
   em `freight` (dono do recurso pai), nunca em `shared.collaboration` (que continua sem saber quem
   a consome, D186).
3. `CreateTripAttachmentHandler` exige `freight.trip.edit` (editar o dono) + `storage.attachment.
   create` — duas permissões, checadas explicitamente no Handler (a segunda não é RBAC de rota, é
   checada via `AuthorizationService` direto, já que `require_permission` só resolve uma por rota).
   `CreateTripCommentHandler` exige `freight.trip.view`/`.view_own` (ver o dono basta, comentar não
   é editar, `081` é explícito) + `storage.comment.create`.
4. `UpdateTripCommentHandler`/`DeleteTripCommentHandler` checam `comment.usuario_id == actor.
   user_id` primeiro (`403` se não, mesmo com `storage.comment.edit_own` concedido — "own" é
   sempre reforçado no Handler, nunca só no nome do código de permissão, mesmo princípio de
   `freight.trip.view_own` em Mobile).

## `AuditMetadata` parcial (D400-family)

`anexos`/`comentarios` não têm `atualizado_em`/`atualizado_por` — `AttachmentResponse.audit`/
`CommentResponse.audit` preenchem `updated_at = created_at`/`updated_by = created_by` (nunca refletem
uma edição real de Comment, já que não há coluna para isso) — mesma disciplina já usada para
`Delivery.audit` (D381) e `CTeResponse.audit` (D400), documentada aqui, não inventada em silêncio.
`anexos` não tem `criado_por` como `NOT NULL` mas o índice não impõe; `comentarios` não tem
`criado_por` nenhuma — `Comment.audit.created_by` é sempre o próprio `usuario_id` (única identidade
que a linha guarda).

## Global Search (082)

`modules/search/` novo — só `application/queries/global_search.py`, sem domain/infrastructure
próprios (é puro agregador, D317). Consulta cada tipo habilitado (tabela do contrato) com um
`ILIKE`/full-text simples sobre o campo já indicado, aplicando a MESMA query `list_page`/permissão
já usada pelo endpoint direto daquele tipo (nunca uma segunda query solta) — `viagem` reusa
`ListTripsHandler` internamente com `codigo__ilike=q`, por exemplo, filtrado pela permissão do
chamador já resolvida por `AuthorizationService.get_permission_codes`. Tipo sem a permissão
correspondente é simplesmente omitido do agrupamento de resposta — nunca `403` (D317 é explícito).

## Timeline — extensão de `019-trip-timeline.md` (083)

`GET /viagens/{id}/timeline` (Lote 4) ganha duas fontes novas na composição: Attachments e Comments
da Viagem, intercalados por `criado_em` com as entradas já existentes (status history, eventos).
Edição em `modules/freight/application/queries/get_trip_timeline.py` (já existente) — nunca um
endpoint novo, exatamente como `083-timelines.md` prescreve.

## Auditorias deste lote (candidatas, confirmadas na Application antes do teste)

1. **Dono determina o contexto, nunca o cliente** — não existe rota genérica `POST /attachments`
   aceitando `entity_type` livre; só `/viagens/{id}/attachments` existe no router.
2. **Hard delete real, primeira vez no projeto** — `DELETE` de Attachment/Comment remove a linha de
   verdade (verificado via `SELECT` direto pós-`DELETE`, não só `404` num próximo `GET`) — todo
   outro `DELETE` do sistema até este lote é soft delete; teste dedicado prova a diferença.
3. **`edit_own`/`delete_own` reforçado no Handler** — outro usuário com `storage.comment.edit_own`
   tentando editar comentário alheio recebe `403`, nunca `200`.
4. **Busca nunca vaza tipo sem permissão** — usuário sem `crm.client.view` buscando um termo que
   bateria em `cliente` e `viagem` só recebe o agrupamento `viagem`, silenciosamente.
5. **`storage_key`/binário nunca aparecem em Attachment** — só `file_id`.

## Achados deste lote

Todas as 5 auditorias candidatas confirmadas por teste real (`test_transversais_flow.py`):
`POST /attachments`/`POST /comments` genéricos de fato não existem em nenhum router; `DELETE` de
Attachment/Comment provado como hard delete real via `SELECT` direto pós-`DELETE` (linha
efetivamente ausente do banco, não só `404` num `GET` seguinte — primeira vez que esse padrão de
prova é necessário no projeto, já que todo `DELETE` anterior era soft delete); `edit_own`/
`delete_own` reforçado no Handler mesmo com um segundo usuário do mesmo tenant tendo o código de
permissão concedido (`403 STORAGE_COMMENT_NOT_OWNED`); Busca Global nunca vaza o tipo `viagem` para
um usuário sem `freight.trip.view`, mesmo achando o termo exato; `storage_key` confirmado ausente da
resposta de `Attachment`/`File`. A extensão da Timeline (D416) também provada — Anexo/Comentário
aparecem como `ANEXO`/`COMENTARIO` em `GET /viagens/{id}/timeline` sem exigir endpoint novo.
