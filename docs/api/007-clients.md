# 007 — Clients

Bounded context proprietário: `crm` (D215).

## Sub-recursos deste dono

- **Endereços**: `GET/POST /clients/{id}/addresses`, `GET/PATCH/DELETE
  /clients/{id}/addresses/{addressId}` — padrão compartilhado, documentado uma única vez em
  [`011-addresses.md`](./011-addresses.md) (D225 — não duplicado aqui).
- **Contatos**: `GET/POST /clients/{id}/contacts`, `GET/PATCH/DELETE
  /clients/{id}/contacts/{contactId}` — ver [`012-contacts.md`](./012-contacts.md). Diferente de
  Endereço, Contato **não é polimórfico** (`contatos_cliente.cliente_id`, FK direta, exclusivo de
  Cliente) e tem seu próprio conjunto de Permissões em `RBAC_MATRIX.md`
  (`crm.client_contact.*`) — qualifica como sub-recurso de fato (D225: ciclo de vida e autorização
  próprios).

## Schema `Client`

```yaml
Client:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "CLI-000456" }
    razao_social: { type: string }
    nome_fantasia: { type: string, nullable: true }
    document: { type: string, description: "`cnpj_cpf` — aceita CNPJ ou CPF (cliente pessoa física)." }
    telefone: { type: string, nullable: true }
    email: { type: string, format: email, nullable: true }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, razao_social, document, status, audit]
```

## `GET /api/v1/clients`

**Segurança**: `bearerAuth` + `crm.client.view`.

**Query parameters**

| Parâmetro | Existe fisicamente? | Ref |
|---|---|---|
| `page`, `limit` | Sim — Offset (Master Data, `PAGINATION.md`) | `components/parameters.md` |
| `status` | Sim — `clientes.status` (`ATIVO`/`INATIVO`) | `components/parameters.md` |
| `document` | Sim — `clientes.cnpj_cpf` (`uq_clientes_tenant_id_cnpj_cpf`) | Específico |
| `search` | Sim — `razao_social`/`nome_fantasia` (`__contains`) | `components/parameters.md` |
| `created_from`/`created_to` | Sim — `criado_em` (atalho de range, `FILTERING_SORTING.md`) | Específico |

D226 — todo filtro acima corresponde a uma coluna real de `clientes` (`relational/002-cadastros.md`,
`INDEXES.md` categoria 4) — nenhum filtro especulativo.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `Client` (D228 — `meta.pagination` sempre presente) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `GET /api/v1/clients/{id}`

**Segurança**: `bearerAuth` + `crm.client.view`.

**Responses**: `200` (`Client`), `401`, `403`, `404` (`CRM_CLIENT_NOT_FOUND`), `500`.

## `POST /api/v1/clients`

**Segurança**: `bearerAuth` + `crm.client.create`.

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          razao_social: { type: string }
          nome_fantasia: { type: string }
          document: { type: string }
          telefone: { type: string }
          email: { type: string, format: email }
        required: [razao_social, document]
```

`tenant_id` nunca é aceito (D208/D218) — resolvido pelo contexto autenticado. `codigo` nunca é
aceito — gerado pela aplicação (`configuracoes_numeracao`, mesmo padrão de `006-branches.md`).

**Responses**

| Código | Corpo |
|---|---|
| `201` | `Client` criado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `409` | `Conflict` (D230) — `CRM_CLIENT_DOCUMENT_ALREADY_EXISTS` (`uq_clientes_tenant_id_cnpj_cpf`) |
| `500` | `InternalServerError` |

## `PATCH /api/v1/clients/{id}`

**Segurança**: `bearerAuth` + `crm.client.edit`. D229 — altera só os campos enviados.

**Responses**: `200` (`Client`), `400`, `401`, `403`, `404`, `409` (D230), `500`.

## `DELETE /api/v1/clients/{id}`

**D219 — soft delete**, nunca `DELETE` físico.

**Segurança**: `bearerAuth` + `crm.client.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `CRM_CLIENT_HAS_ACTIVE_TRIPS` (regra de negócio:
não modelada como constraint física; a Aplicação decide se um Cliente com Viagem em andamento pode
ser desativado — fora do escopo deste lote decidir a regra exata, só reservar o código de erro),
`500`.

## Fora de escopo deste lote (não esquecido)

- `crm.client.export`/`crm.client.comment` já existem em `RBAC_MATRIX.md` mas não têm endpoint
  aqui — exportação (`exportacoes_geradas`, já modelada) e comentário (`comentarios`, polimórfico,
  D186) merecem seu próprio tratamento quando esses fluxos entrarem num lote dedicado, mesmo
  raciocínio já usado para `identity_access.user.reset_password` no Lote 2.

## Como este documento cresce

Nenhuma mudança prevista até o Lote 4 (Viagens) referenciar `Client` como FK de `Viagem` — nesse
ponto, `007-clients.md` só é referenciado (`$ref`), nunca redefinido.
