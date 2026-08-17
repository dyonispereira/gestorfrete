# 006 — Branches

Bounded context proprietário: `tenancy` (D215).

**Emenda (D231, Lote 3)**: `endereco` deixou de ser campo embutido do recurso `Branch`. O que
existia até o Lote 2 (`filiais.endereco` JSONB) era redundante com o padrão polimórfico já previsto
para Filial desde D182 — corrigido na origem (`relational/001-core.md`/`002-cadastros.md`). Endereço
de Filial agora é sub-recurso, mesmo padrão de Cliente/Fornecedor — ver
[`011-addresses.md`](./011-addresses.md): `GET/POST /branches/{id}/addresses`,
`GET/PATCH/DELETE /branches/{id}/addresses/{addressId}`.

## `GET /api/v1/branches`

**Segurança**: `bearerAuth` + `tenancy.branch.view`.

**Query parameters**: `page`, `limit`, `search` (busca em `nome`/`codigo`) — `components/parameters.md`.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `Branch` (`components/schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `GET /api/v1/branches/{id}`

**Segurança**: `bearerAuth` + `tenancy.branch.view`.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Branch` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — `TENANCY_BRANCH_NOT_FOUND` |
| `500` | `InternalServerError` |

## `POST /api/v1/branches`

**Segurança**: `bearerAuth` + `tenancy.branch.create`.

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
          is_headquarters: { type: boolean, default: false }
        required: [nome]
```

Endereço não é criado junto — a Filial nasce sem endereço, adicionado depois via
`POST /branches/{id}/addresses` (`011-addresses.md`). Mesmo fluxo em duas etapas já natural para
Cliente/Fornecedor (um recurso com ciclo de vida próprio não precisa nascer completo no mesmo
`POST` do pai).

**Responses**

| Código | Corpo |
|---|---|
| `201` | `Branch` criado — `Location: /api/v1/branches/{id}` |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `409` | `Conflict` — `TENANCY_BRANCH_CODE_ALREADY_EXISTS` (`uq_filiais_tenant_id_codigo`), ou `TENANCY_HEADQUARTERS_ALREADY_EXISTS` se `is_headquarters: true` e já existir uma matriz (`uq_filiais_tenant_id_matriz`, índice único parcial — `CONSTRAINTS.md`) |
| `500` | `InternalServerError` |

`codigo` (não presente no corpo acima) é gerado pela aplicação seguindo a
`Configuração de Numeração` do tenant (`configuracoes_numeracao`, `010-administracao.md`) — nunca
informado pelo cliente na criação, consistente com D175 (identificador funcional gerido pela
plataforma/tenant, não digitado livremente em toda tabela que o usa dessa forma).

## `PATCH /api/v1/branches/{id}`

**Segurança**: `bearerAuth` + `tenancy.branch.edit`.

**Request**: mesmo corpo de `POST`, todos os campos opcionais.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Branch` atualizado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `409` | `Conflict` — mesmo conjunto de `POST` (`TENANCY_HEADQUARTERS_ALREADY_EXISTS` se tentar marcar uma segunda Filial como matriz) |
| `500` | `InternalServerError` |

## `DELETE /api/v1/branches/{id}`

**D219 — nunca `DELETE` físico** (soft delete, D177).

**Segurança**: `bearerAuth` + `tenancy.branch.delete`.

**Responses**

| Código | Corpo |
|---|---|
| `204` | Sem corpo |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `422` | `UnprocessableEntity` — `TENANCY_CANNOT_DELETE_HEADQUARTERS` (não modelado como constraint física — decisão de produto se a matriz pode ou não ser excluída antes de outra ser promovida; tratado como regra de Application/Domínio, não de banco) |
| `500` | `InternalServerError` |

## Como este documento cresce

Vínculo Filial↔Centro de Custo (`centros_custo.filial_id`, já físico) e Filial↔Veículo
(`veiculos_tracionadores.filial_id`, já físico) ganham parâmetros de filtro próprios
(`?branch_id=`) nos endpoints de Cadastros/Frota quando esses lotes chegarem — não antecipados
aqui.
