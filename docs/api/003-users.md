# 003 — Users

Bounded context proprietário: `identity_access` (D215).

## Achado ao preparar este documento (D222)

O filtro `?branch=` pedido para este lote **não é implementado** — `usuarios` não tem `filial_id`
nem qualquer vínculo (direto ou transitivo via `funcionarios`) a `filiais` no Modelo Relacional
(verificado por `grep`, não assumido). Diferente do filtro `?role=`, que só precisava da tabela de
junção `usuarios_papeis` (criada agora, D222 — ver `relational/001-core.md`), aqui não existe
nenhuma coluna física para filtrar — inventar o filtro sem a coluna existir seria mentir sobre a
capacidade real da API. Registrado como lacuna aberta: se o produto precisar de "Usuário por
Filial", a modelagem começa pelo Domain Model (D101), não por adicionar um filtro que a API não
consegue de fato resolver.

## `GET /api/v1/users`

**Segurança**: `bearerAuth` + `identity_access.user.view`.

**Query parameters**

| Parâmetro | Ref | Descrição |
|---|---|---|
| `page`, `limit` | `components/parameters.md` | Paginação Offset (Master Data, `PAGINATION.md`) |
| `status` | `components/parameters.md` (`StatusFilterParam`) | Valores: `ATIVO`/`INATIVO`/`BLOQUEADO` |
| `role` | Específico deste endpoint | Filtra por `papel_id` (via `usuarios_papeis`, D222) — aceita `UUID` do Papel |
| `search` | `components/parameters.md` | Busca em `nome`/`email` (`__contains`, `FILTERING_SORTING.md`) |
| `expand` | `components/parameters.md` | `?expand=roles` — expande `roles` de array de IDs para `RoleSummary` (`{id, nome}`) |

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `User` (`components/schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `GET /api/v1/users/{id}`

**Segurança**: `bearerAuth` + `identity_access.user.view`.

**Path parameters**: `IdPathParam` (`components/parameters.md`).

**Responses**

| Código | Corpo |
|---|---|
| `200` | `User` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — `IDENTITY_USER_NOT_FOUND` |
| `500` | `InternalServerError` |

## `POST /api/v1/users`

**Segurança**: `bearerAuth` + `identity_access.user.create`.

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
          email: { type: string, format: email }
          password: { type: string, format: password, minLength: 8 }
          driver_id: { $ref: "#/components/schemas/UUID", nullable: true }
          employee_id: { $ref: "#/components/schemas/UUID", nullable: true }
          role_ids:
            type: array
            items: { $ref: "#/components/schemas/UUID" }
            description: Papéis atribuídos na criação — grava em `usuarios_papeis` (D222); pode
              vir vazio (usuário sem Papel, sem nenhuma Permissão até ser atribuído depois).
        required: [nome, email, password]
```

`driver_id`/`employee_id`: no máximo um preenchido — mesma regra do banco
(`ck_usuarios_motorista_xor_funcionario`, `CONSTRAINTS.md`), validada também na Application antes
de chegar ao banco (erro `422` mais claro que deixar a constraint física rejeitar).

**Responses**

| Código | Corpo |
|---|---|
| `201` | `User` criado — header `Location: /api/v1/users/{id}` |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `409` | `Conflict` — `IDENTITY_EMAIL_ALREADY_EXISTS` (`uq_usuarios_tenant_id_email`) |
| `422` | `UnprocessableEntity` — `IDENTITY_USER_DRIVER_AND_EMPLOYEE_CONFLICT` |
| `500` | `InternalServerError` |

## `PATCH /api/v1/users/{id}`

**Segurança**: `bearerAuth` + `identity_access.user.edit`.

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
          email: { type: string, format: email }
          role_ids:
            type: array
            items: { $ref: "#/components/schemas/UUID" }
            description: Substitui o conjunto de Papéis do Usuário (todas as linhas de
              `usuarios_papeis` para este usuario_id são recalculadas para bater com esta lista) —
              nunca um "adicionar um Papel" incremental neste mesmo campo; ver nota abaixo.
```

Alterar `password`/redefinir senha de outro usuário usa `identity_access.user.reset_password`
(permissão diferente, criticidade Alta) — **não é este endpoint**; fica para um endpoint próprio
(`POST /users/{id}/reset-password`) quando esse fluxo administrativo for detalhado, fora do escopo
mínimo deste lote (só CRUD básico + atribuição de Papel, conforme pedido).

**`role_ids` é substituição completa, não incremental**: enviar `["A"]` quando o usuário já tinha
`["A", "B"]` remove `B`. Motivo: `PATCH` semanticamente parcial se aplica aos *campos* do recurso,
mas o valor de um campo-lista é sempre o novo valor completo (mesmo comportamento usado em toda a
API para campos-array, evita ambiguidade sobre "adicionar" vs. "substituir").

**Responses**

| Código | Corpo |
|---|---|
| `200` | `User` atualizado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `409` | `Conflict` — e-mail duplicado |
| `500` | `InternalServerError` |

## `DELETE /api/v1/users/{id}`

**D219 — nunca `DELETE` físico.** Executa exclusão lógica (`excluido_em`/`excluido_por`, D177) —
fisicamente, `usuarios.status` também transiciona para algo equivalente a inativo via a mesma
operação (a API expõe isso como um único comando, a aplicação decide as duas escritas).

**Segurança**: `bearerAuth` + `identity_access.user.deactivate`.

**Responses**

| Código | Corpo |
|---|---|
| `204` | Sem corpo |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `422` | `UnprocessableEntity` — `IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN` (invariante de domínio: não se pode desativar o último Usuário com Papel de Administrador do tenant — regra de negócio, não uma constraint física) |
| `500` | `InternalServerError` |

## Como este documento cresce

`POST /users/{id}/reset-password` e `POST /users/{id}/block` (usando
`identity_access.user.reset_password`/`.block`, já existentes em `RBAC_MATRIX.md` mas sem endpoint
neste lote) entram num lote futuro de "Segurança de Conta" quando o fluxo administrativo completo
for detalhado — não inventados agora só porque a Permissão já existe.
