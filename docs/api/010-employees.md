# 010 — Employees

Bounded context proprietário: `identity_access` (D215) — mesmo dono de Usuário/Papel/Permissão
(`RBAC_MATRIX.md` 7.4), não `crm`/`maintenance` como Cliente/Fornecedor.

## Nota de origem (D196)

`Funcionário` só existe fisicamente desde a Sprint 09 (`relational/002-cadastros.md`) — a tabela
foi criada retroativamente ao preparar `FOREIGN_KEYS.md`, quando se descobriu que
`usuarios.funcionario_id` já referenciava uma tabela que nunca tinha sido materializada, apesar de
o Domain Model já descrever `Funcionário` em detalhe desde antes. Este é o primeiro endpoint sobre
essa tabela.

## Relação com Usuário

`usuarios.funcionario_id` é **opcional** e **exclusivo** com `motorista_id`
(`ck_usuarios_motorista_xor_funcionario`, `003-users.md`) — um Funcionário pode existir sem nunca
ter um Usuário de acesso ao sistema (ex.: um mecânico que só é gerenciado como Funcionário, nunca
loga no ERP). A associação é sempre feita do lado de `Usuário`
(`POST/PATCH /users` com `employee_id`, `003-users.md`) — **não há** `PATCH
/employees/{id}` com um campo `user_id`; a direção da FK física é `usuarios → funcionarios`, a API
respeita essa direção, nunca simula o inverso.

## Schema `Employee`

```yaml
Employee:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "FUNC-000045" }
    nome: { type: string }
    cargo: { type: string }
    hired_at: { type: string, format: date, nullable: true, description: "`data_admissao`." }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, cargo, status, audit]
```

## `GET /api/v1/employees`

**Segurança**: `bearerAuth` + `identity_access.employee.view`.

**Query parameters**: `page`/`limit`, `status`, `search` (`nome`/`cargo`), `created_from`/
`created_to`.

**Responses**: `200` (`Pagination` de `Employee`), `401`, `403`, `500`.

## `GET /api/v1/employees/{id}`

**Segurança**: `identity_access.employee.view`. **Responses**: `200`, `401`, `403`, `404`
(`IDENTITY_EMPLOYEE_NOT_FOUND`), `500`.

## `POST /api/v1/employees`

**Segurança**: `identity_access.employee.create`.

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
          hired_at: { type: string, format: date }
        required: [nome, cargo]
```

**Responses**: `201`, `400`, `401`, `403`, `500` — **sem `409`**: `funcionarios` não tem `UNIQUE`
além de `(tenant_id, codigo)` gerado pela aplicação (não há CPF/documento único modelado para
Funcionário no Modelo Relacional — diferente de Cliente/Fornecedor/Motorista); registrado aqui como
observação, não uma correção (não é escopo deste lote decidir se Funcionário precisa de CPF único).

## `PATCH /api/v1/employees/{id}`

**Segurança**: `identity_access.employee.edit`. D229 — parcial.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## `DELETE /api/v1/employees/{id}`

**D219 — soft delete.** **Segurança**: `identity_access.employee.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER` (regra
de Aplicação: desativar um Funcionário ainda vinculado a um Usuário `ATIVO` exige desvincular ou
desativar o Usuário primeiro — não modelado como constraint física), `500`.

## Como este documento cresce

Nenhum sub-recurso previsto — `Funcionário` é mais simples que `Motorista` (sem documentos, sem
aptidão calculada). Se o produto precisar de algo equivalente a `documentos_motorista` para
Funcionário, entra pelo Domain Model primeiro (D101).
