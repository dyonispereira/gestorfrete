# 013 — Cost Centers

Bounded context proprietário: `financial` (D215) — apesar de `centros_custo` viver fisicamente em
`relational/002-cadastros.md` (Cadastros), a posse RBAC é de `financial`
(`financial.cost_center.*`, `RBAC_MATRIX.md` seção 7.18) — o endpoint segue a posse real, mesma
nota já registrada em `008-suppliers.md` para Fornecedor/`maintenance`.

## Centro de Custo é cadastro mestre puro — nunca carrega saldo/indicador

Reforço direto de D090 (indicadores/agregados nunca em tabela operacional, só em `analytics`) já
aplicado desde a modelagem física (`relational/002-cadastros.md`: "`centros_custo` guarda só
identidade e classificação — nenhuma coluna de saldo, indicador ou valor acumulado"). A API segue a
mesma regra: **nenhum campo de saldo/resultado/indicador no schema `CostCenter`** — qualquer "custo
por Centro de Custo" é uma consulta separada, futura, contra `analytics`/`rateios_despesa`, nunca um
campo somado aqui.

## Schema `CostCenter`

```yaml
CostCenter:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "CC-000012" }
    accounting_code: { type: string, description: "`codigo_contabil`." }
    nome: { type: string }
    branch_id:
      $ref: "#/components/schemas/UUID"
      nullable: true
      description: "`filial_id`, opcional — Centro de Custo pode não estar vinculado a nenhuma
        Filial específica."
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, accounting_code, nome, status, audit]
```

## `GET /api/v1/cost-centers`

**Segurança**: `bearerAuth` + `financial.cost_center.view`.

**Query parameters**: `page`/`limit`, `status`, `branch_id` (`filial_id`, existe fisicamente —
D226), `search` (`nome`/`codigo_contabil`).

**Responses**: `200` (`Pagination` de `CostCenter`), `401`, `403`, `500`.

## `GET /api/v1/cost-centers/{id}`

**Segurança**: `financial.cost_center.view`. **Responses**: `200`, `401`, `403`, `404`
(`FINANCIAL_COST_CENTER_NOT_FOUND`), `500`.

## `POST /api/v1/cost-centers`

**Segurança**: `financial.cost_center.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          accounting_code: { type: string }
          nome: { type: string }
          branch_id: { $ref: "#/components/schemas/UUID" }
        required: [accounting_code, nome]
```

**Responses**: `201`, `400`, `401`, `403`, `409` (D230 — `FINANCIAL_COST_CENTER_CODE_ALREADY_EXISTS`,
`uq_centros_custo_tenant_id_codigo_contabil`), `500`.

## `PATCH /api/v1/cost-centers/{id}`

**Segurança**: `financial.cost_center.edit`. D229 — parcial.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## Sem `DELETE` — nunca implementado neste lote

`RBAC_MATRIX.md` **não tem** `financial.cost_center.delete` (confirmado por grep, não assumido —
só `.view`/`.create`/`.edit` existem). D216 proíbe inventar o código; sem a Permissão, não há
endpoint. Desativação é via `PATCH` (`status: INATIVO`) — coerente com um Centro de Custo já
referenciado por lançamentos financeiros históricos (`rateios_despesa`) nunca poder desaparecer,
só deixar de aceitar novos lançamentos.

## Como este documento cresce

Se o produto decidir que Centro de Custo precisa de exclusão real, a Permissão nasce primeiro em
`RBAC_MATRIX.md` (registrada como decisão), só então o endpoint é adicionado aqui — nunca o
contrário.
