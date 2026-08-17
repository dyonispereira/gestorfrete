# 012 — Contacts

Bounded context proprietário: `crm` (D215) — mesmo dono de Cliente, permissão própria e dedicada
(`crm.client_contact.*`, distinta de `crm.client.*`).

## Por que Contato é sub-recurso só de Cliente, nunca polimórfico

Diferente de Endereço (D182/D186, compartilhado entre Cliente/Fornecedor/Filial), `Contato` não é
polimórfico no Modelo Relacional — `contatos_cliente.cliente_id` é uma FK direta e exclusiva
(`relational/002-cadastros.md`). Não existe `Contato de Fornecedor` nem `Contato de Filial` no
Domain Model. A API reflete exatamente essa assimetria (D227 — nunca inventa uma associação que o
domínio não tem): só existe `/clients/{id}/contacts`, nunca `/suppliers/{id}/contacts` nem uma rota
polimórfica genérica.

```
GET/POST         /api/v1/clients/{id}/contacts
GET/PATCH/DELETE /api/v1/clients/{id}/contacts/{contactId}
```

## Schema `Contact`

```yaml
Contact:
  type: object
  description: "`audit` aqui só tem `created_at`/`updated_at` — `contatos_cliente` não tem colunas
    `criado_por`/`atualizado_por` no Modelo Relacional (auditoria mais leve que a maioria das
    tabelas, D217 reflete exatamente o que a tabela tem, nunca inventa um campo que não existe)."
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    nome: { type: string }
    cargo: { type: string, nullable: true }
    telefone: { type: string, nullable: true }
    email: { type: string, format: email, nullable: true }
    created_at: { $ref: "#/components/schemas/Timestamp" }
    updated_at: { $ref: "#/components/schemas/Timestamp" }
  required: [id, nome, created_at, updated_at]
```

## `GET /api/v1/clients/{id}/contacts`

**Segurança**: `bearerAuth` + `crm.client_contact.view`.

**Responses**: `200` (`Pagination` de `Contact`), `401`, `403`, `404` (Cliente não existe), `500`.

## `POST /api/v1/clients/{id}/contacts`

**Segurança**: `crm.client_contact.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
          cargo: { type: string }
          telefone: { type: string }
          email: { type: string, format: email }
        required: [nome]
```

**Responses**: `201`, `400`, `401`, `403`, `404`, `500` — **sem `409`**: nenhuma `UNIQUE` em
`contatos_cliente` além do `id` técnico (mais de um Contato pode ter o mesmo e-mail/telefone, sem
restrição física).

## `PATCH /api/v1/clients/{id}/contacts/{contactId}`

**Segurança**: `crm.client_contact.edit`. D229 — parcial.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## `DELETE /api/v1/clients/{id}/contacts/{contactId}`

**D219 — soft delete** (`contatos_cliente.excluido_em`, embora sem `excluido_por` — mesma nota de
auditoria leve acima).

**Segurança**: `crm.client_contact.delete`. **Responses**: `204`, `401`, `403`, `404`, `500` — sem
`422`: nenhuma regra de negócio bloqueia a exclusão de um Contato (diferente de excluir o próprio
Cliente).

## Como este documento cresce

Se `Contato` precisar existir para outro dono no futuro, a decisão nasce no Domain Model (D101) —
o Modelo Relacional ganharia `entidade_tipo`/`entidade_id` polimórfico (mesma reforma que
`Endereço` já passou, D182), só então a API seguiria.
