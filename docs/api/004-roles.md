# 004 — Roles

Bounded context proprietário: `identity_access` (D215). **Nenhum endpoint altera Permissão
diretamente em Usuário** — atribuição é sempre Usuário→Papel (`003-users.md`, `role_ids`) e
Papel→Permissão (`permissions` neste documento) — nunca um atalho que ligue Usuário a Permissão sem
passar por Papel (reforça a própria estrutura do RBAC, D053/D060).

## `GET /api/v1/roles`

**Segurança**: `bearerAuth` + `identity_access.role.view`.

**Query parameters**: `page`, `limit` (`components/parameters.md`), `search` (busca em `nome`).

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `Role` (`components/schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `GET /api/v1/roles/{id}`

**Segurança**: `bearerAuth` + `identity_access.role.view`.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Role` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — `IDENTITY_ROLE_NOT_FOUND` |
| `500` | `InternalServerError` |

## `POST /api/v1/roles`

**Segurança**: `bearerAuth` + `identity_access.role.create`.

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
          descricao: { type: string, nullable: true }
          permissions:
            type: array
            items: { type: string }
            description: Códigos de Permissão (ex. "identity_access.user.view") — D216, cada
              código precisa existir em RBAC_MATRIX.md; código inexistente é erro de validação,
              nunca criado on-the-fly.
        required: [nome]
```

**Responses**

| Código | Corpo |
|---|---|
| `201` | `Role` criado — `Location: /api/v1/roles/{id}` |
| `400` | `BadRequest` — inclui `permissions` com um código que não existe em `RBAC_MATRIX.md` (`error.code = IDENTITY_UNKNOWN_PERMISSION_CODE`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `409` | `Conflict` — `IDENTITY_ROLE_NAME_ALREADY_EXISTS` (`uq_papeis_tenant_id_nome`) |
| `500` | `InternalServerError` |

## `PATCH /api/v1/roles/{id}`

**Segurança**: `bearerAuth` + `identity_access.role.edit`.

**Request**: mesmo corpo de `POST`, todos os campos opcionais. `permissions`, quando enviado, é
substituição completa (mesmo comportamento de `role_ids` em `003-users.md` — lista sempre
representa o valor final, nunca incremental).

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Role` atualizado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `409` | `Conflict` — nome duplicado |
| `500` | `InternalServerError` |

## `DELETE /api/v1/roles/{id}`

**D219 — nunca `DELETE` físico** (soft delete, D177).

**Segurança**: `bearerAuth` + `identity_access.role.delete`.

**Responses**

| Código | Corpo |
|---|---|
| `204` | Sem corpo |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `422` | `UnprocessableEntity` — `IDENTITY_ROLE_IN_USE` (Papel ainda atribuído a algum Usuário via `usuarios_papeis`, D222 — a aplicação bloqueia a exclusão, não deixa o Usuário órfão de Papel silenciosamente) |
| `500` | `InternalServerError` |

## Como este documento cresce

Uma futura tela de "sugestão de Papel por hierarquia" (`RBAC_MATRIX.md` seção 9 — Administrador/
Diretor/Gerente/Supervisor/Analista/Operacional, já usada em `SEED_DATA.md` para Tenant Bootstrap)
pode ganhar um endpoint próprio (`GET /roles/suggestions`) quando o produto decidir formalizar
esse fluxo — não inventado agora, fora do escopo de CRUD básico deste lote.
