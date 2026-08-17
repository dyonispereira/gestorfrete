# 008 — Suppliers

Bounded context proprietário: `maintenance` (D215) — apesar do nome genérico "Fornecedor", a
posse em `RBAC_MATRIX.md` é `maintenance` (`maintenance.supplier.*`), não `crm`; o endpoint segue a
posse real, não a intuição de nome (D215 é sobre o dono de fato, não o que "parece" fazer sentido).

## Categorias — um único recurso, nunca um endpoint por categoria

`fornecedores.tipo_principal` (`fornecedores_tipo_principal_enum`) já cobre oficina, posto,
seguradora, borracharia, guincho, autopeças (`PECA`) e demais fornecedores (`OUTRO`) — D076 (não
duplicar por categoria, mesmo princípio já aplicado no Modelo Relacional) continua valendo na API:
**um único `GET /suppliers?category=OFICINA`**, nunca `/suppliers/workshops`,
`/suppliers/gas-stations`, etc.

## Schema `Supplier`

```yaml
Supplier:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "FOR-000789" }
    razao_social: { type: string }
    cnpj: { type: string }
    telefone: { type: string, nullable: true }
    category:
      type: string
      nullable: true
      enum: [PECA, RECAPAGEM, SEGURO, OFICINA, POSTO, BORRACHARIA, GUINCHO, OUTRO]
      description: "`tipo_principal` — opcional na base, um Fornecedor pode não ter categoria
        principal definida."
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, razao_social, cnpj, status, audit]
```

## Sub-recurso

- **Endereços**: `GET/POST /suppliers/{id}/addresses`, mesmo padrão compartilhado de
  [`011-addresses.md`](./011-addresses.md).
- Sem sub-recurso de Contato — `RBAC_MATRIX.md` só modela `crm.client_contact.*` (Cliente); não
  existe `Contato de Fornecedor` no Domain Model, e a API não inventa um (D227).

## `GET /api/v1/suppliers`

**Segurança**: `bearerAuth` + `maintenance.supplier.view`.

**Query parameters**: `page`/`limit`, `status`, `category` (`tipo_principal`, existe fisicamente —
D226), `search` (`razao_social`), `created_from`/`created_to`.

**Responses**: `200` (`Pagination` de `Supplier`), `401`, `403`, `500`.

## `GET /api/v1/suppliers/{id}`

**Segurança**: `maintenance.supplier.view`. **Responses**: `200`, `401`, `403`, `404`
(`MAINTENANCE_SUPPLIER_NOT_FOUND`), `500`.

## `POST /api/v1/suppliers`

**Segurança**: `maintenance.supplier.create`.

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
          telefone: { type: string }
          category:
            type: string
            enum: [PECA, RECAPAGEM, SEGURO, OFICINA, POSTO, BORRACHARIA, GUINCHO, OUTRO]
        required: [razao_social, cnpj]
```

**Responses**: `201`, `400`, `401`, `403`, `409` (D230 — `MAINTENANCE_SUPPLIER_CNPJ_ALREADY_EXISTS`,
`uq_fornecedores_tenant_id_cnpj`), `500`.

## `PATCH /api/v1/suppliers/{id}`

**Segurança**: `maintenance.supplier.edit`. D229 — parcial. **Responses**: `200`, `400`, `401`,
`403`, `404`, `409`, `500`.

## `DELETE /api/v1/suppliers/{id}`

**D219 — soft delete.** **Segurança**: `maintenance.supplier.delete`. **Responses**: `204`, `401`,
`403`, `404`, `422` — `MAINTENANCE_SUPPLIER_HAS_OPEN_ORDERS` (Fornecedor com Ordem de Serviço em
aberto — regra de Aplicação, não constraint física), `500`.

## Fora de escopo deste lote

`maintenance.supplier.export`/`.comment` — mesma nota de `007-clients.md`, adiados para um lote de
exportação/comentário compartilhado entre recursos.

## Como este documento cresce

`Supplier` é referenciado (nunca redefinido) quando `ordens_servico.fornecedor_executor_id` e
`contas_pagar.fornecedor_id` ganharem seus próprios endpoints (Lote de Manutenção/Financeiro).
