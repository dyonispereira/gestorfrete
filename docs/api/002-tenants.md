# 002 — Tenants

Bounded context proprietário: `tenancy` (D215). **Um usuário normal nunca seleciona outro Tenant** —
`GET`/`PATCH /tenant` sempre resolvem para o tenant do contexto autenticado (D208/D218), nunca
aceitam um identificador de tenant na URL ou no corpo. Não há `GET /tenants` (plural, listagem) —
propositalmente singular: do ponto de vista de qualquer chamada autenticada, só existe "o" tenant
atual.

Operação cross-tenant (equipe GestorFrete administrando múltiplos tenants,
[`../product/RBAC_MATRIX.md`](../product/RBAC_MATRIX.md) seção 7.26) **não pertence a este lote** —
vive numa superfície de API Interna própria (`OPENAPI_ARCHITECTURE.md` seção 2), com suas próprias
permissões, nunca reaproveitando este endpoint singular.

## `GET /api/v1/tenant`

**Segurança**: `bearerAuth` + `tenancy.company_data.view`.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Tenant` (`components/schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `500` | `InternalServerError` |

## `PATCH /api/v1/tenant`

**Segurança**: `bearerAuth` + `tenancy.company_data.edit`.

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
          cnpj: { type: string }
        # nenhum campo obrigatório — PATCH é sempre parcial (NAMING_CONVENTION.md seção 5)
```

`status` **nunca** é aceito neste corpo — é `readOnly` (`components/schemas.md`), governado pelo
fluxo de assinatura/cobrança, não por este endpoint.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Tenant` atualizado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `409` | `Conflict` — `TENANCY_CNPJ_ALREADY_EXISTS` (violação de `uq_tenants_cnpj`, embora extremamente raro mudar de CNPJ) |
| `422` | `UnprocessableEntity` — CNPJ com formato/dígito verificador inválido |
| `500` | `InternalServerError` |

## O que este lote não cobre (fora de escopo, não esquecido)

- `configuracoes_regionais_tenant` (fuso/idioma/moeda) e `configuracoes_personalizacao`
  (White Label) são tabelas próprias, distintas de `tenants` — endpoints
  `GET/PATCH /tenant/settings/regional` e `/tenant/settings/branding` ficam para um lote futuro,
  não inventados aqui só porque "parecem parte do Tenant" (D076 aplicado à API).
- `recursos_habilitados_tenant` (features do Plano) é somente leitura derivada do Plano contratado
  — não há endpoint de edição (o tenant não escolhe suas próprias features livremente).

## Como este documento cresce

Novo endpoint de configuração do tenant (regional/branding) ganha seu próprio arquivo
(`00N-tenant-settings.md`) quando o lote correspondente chegar — nunca inflando este documento além
do que `tenants` (a tabela) realmente é.
