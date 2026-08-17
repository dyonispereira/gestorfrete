# 005 — Permissions

Bounded context proprietário: `identity_access` (D215). Platform Reference Data (D046,
`permissoes` sem `tenant_id`) — **somente leitura para clientes normais**. `POST`/`PATCH`/`DELETE`
de Permissão pertencem à administração da própria plataforma GestorFrete
([`../product/RBAC_MATRIX.md`](../product/RBAC_MATRIX.md) seção 7.26) — fora da superfície do
produto, fora deste lote (e, quando existirem, vivem na superfície "API Interna",
`OPENAPI_ARCHITECTURE.md` seção 2, nunca aqui).

## `GET /api/v1/permissions`

**Segurança**: `bearerAuth` + `identity_access.permission.view`. Sem escopo de tenant (Platform
Reference Data — mesma lista para todos os tenants).

**Query parameters**

| Parâmetro | Ref | Descrição |
|---|---|---|
| `page`, `limit` | `components/parameters.md` | Paginação Offset — 311 permissões totais (`RBAC_MATRIX.md`), cabe tranquilamente em poucas páginas |
| `module` | Específico deste endpoint | Filtra por `modulo` (ex.: `identity_access`, `tenancy`, `freight`) |
| `search` | `components/parameters.md` | Busca em `nome`/`code` |

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `Permission` (`components/schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `GET /api/v1/permissions/{id}`

**Segurança**: `bearerAuth` + `identity_access.permission.view`.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Permission` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — `IDENTITY_PERMISSION_NOT_FOUND` |
| `500` | `InternalServerError` |

## Por que não há `POST`/`PATCH`/`DELETE` aqui

`permissoes.codigo` nunca é editado nem removido depois de criado (D057) — uma permissão obsoleta é
aposentada (convenção de nome/módulo já registrada em `relational/001-core.md`), nunca apagada. Dar
ao tenant qualquer verbo de escrita sobre este recurso violaria D046 (Platform Reference Data é
"atualizável apenas pela plataforma") — não é uma omissão deste lote, é a regra permanente.

## Como este documento cresce

Se a administração da plataforma (fora deste produto, `RBAC_MATRIX.md` seção 7.26) precisar de uma
API própria para gerenciar o catálogo de Permissões, ela nasce como um documento separado na
superfície "API Interna" — nunca adicionando verbos de escrita a este arquivo.
