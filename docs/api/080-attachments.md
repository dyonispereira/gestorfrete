# 080 — Attachments (Anexos)

Bounded context proprietário: `storage` (D215). `anexos` — infraestrutura polimórfica
compartilhada (D186), mesma tabela física reutilizada por toda entidade com "Anexos suportados"
no Data Dictionary Funcional. `019-trip-timeline.md` (Lote 4) já sinalizava esta lacuna
explicitamente ("Anexos: Não — sem endpoint de API neste lote") — fechada agora.

## D316 — o dono determina o contexto, nunca o cliente

Mesmo princípio de `011-addresses.md` (D225, Lote 3), com uma diferença: `anexos.entidade_tipo` é
**vocabulário de texto extensível** (D120-style), não um Enum físico fechado como
`enderecos_entidade_tipo_enum` — então, ao contrário de Endereço, este documento **não enumera
exaustivamente** todo dono possível (dezenas de entidades têm "Anexos suportados: Sim"). Em vez
disso, define o **padrão único** que qualquer dono já ativado implementa, e ativa explicitamente o
primeiro/principal consumidor:

```
GET/POST         /api/v1/viagens/{id}/attachments
GET/PATCH/DELETE /api/v1/viagens/{id}/attachments/{attachmentId}
```

**Nunca**: `POST /api/v1/attachments` aceitando `entity_type`/`entity_id` livres no corpo — isso
permitiria ao cliente anexar arquivos a qualquer entidade, inclusive fora do vocabulário real
(pedido explícito do usuário, rejeitado por design).

## Schema `Attachment`

Definido em `components/transversal-schemas.md#/Attachment`.

## `GET /{owner}/{id}/attachments`

**Segurança**: `bearerAuth` + a permissão de **visualização** do dono (ex.: `freight.trip.view`/
`.view_own`, resolvendo o `{id}` — `404` se o dono não existe ou não é visível ao chamador) **e**
`storage.attachment.view` — duas camadas, mesmo espírito de D225 aplicado com uma permissão própria
adicional (diferente de Endereço, que não tinha RBAC próprio).

**Responses**: `200` (`Pagination` de `Attachment`), `401`, `403`, `404`, `500`.

## `POST /{owner}/{id}/attachments`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          attachment_type: { type: string }
          file_id: { $ref: "#/components/schemas/UUID" }
          description: { type: string }
        required: [attachment_type, file_id]
```

`file_id` deve referenciar um `File` (`079`) já `ATIVO` — o upload acontece antes, via
`078-storage.md`, nunca dentro deste `POST` (dois passos deliberadamente separados: enviar o
binário, depois vinculá-lo a uma entidade).

**Segurança**: permissão de **edição** do dono + `storage.attachment.create` (App ● — mesmo padrão
de captura de evidência já usado pelo Motorista em `058-driver-deliveries.md`).

**Responses**: `201` (`Attachment`), `400`, `401`, `403`, `404` (dono ou `file_id` não existe),
`500`.

## `DELETE /{owner}/{id}/attachments/{attachmentId}`

**Sem soft delete próprio**: `anexos` não tem `excluido_em`/`excluido_por` (mesma disciplina de
imutabilidade Histórica de D037 já documentada em `003-operacao.md`) — a exclusão remove o vínculo
(`anexos`), o `File` referenciado (`079`) permanece intacto e pode estar vinculado a outras
entidades.

**Segurança**: permissão de edição do dono + `storage.attachment.delete` (Gerente Operacional).

**Responses**: `204`, `401`, `403`, `404`, `500`.

## Sem `PATCH`

`anexos` não tem campo editável além de `descricao` — corrigir o tipo/arquivo de um anexo errado é
excluir e recriar, nunca editar um vínculo já estabelecido (mesmo princípio de D248 aplicado a uma
associação, não a uma vigência).

## Fora de escopo, não esquecido

`Viagem` é o único dono ativado nesta preparação — dezenas de outras entidades têm "Anexos
suportados: Sim" no Data Dictionary Funcional (Entrega, Ocorrência, Assinatura, Ordem de Serviço,
Tenant, etc.), mas ativar cada uma é mecânico e idêntico a este padrão (D225-style), não uma
decisão de design nova. Ativado sob demanda, um dono por vez, quando o módulo correspondente
precisar.

## Como este documento cresce

Novo dono = nova rota `/{recurso}/{id}/attachments` idêntica a esta, mais a linha correspondente em
`components/security.md` apontando para a permissão de visualização/edição daquele dono — nunca uma
segunda forma de anexar arquivos.
