# EMPLOYEE_IMPLEMENTATION.md — `Funcionário` (`modules/identity_access/`)

Contrato: [`../../api/010-employees.md`](../../api/010-employees.md). DDL:
[`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md)
(`funcionarios`). RBAC: `identity_access.employee.*` (`RBAC_MATRIX.md` §7.4).

Novo agregado dentro do bounded context `identity_access` já construído no Lote 2 (mesmo dono de
`Usuário`/`Papel`/`Permissão`) — nenhum módulo novo, `Employee` senta ao lado de `User`/`Role`/
`Permission`/`Session` nas mesmas quatro camadas já existentes.

## Relação com `Usuário` — a FK é sempre `usuarios → funcionarios`, nunca o inverso

`usuarios.funcionario_id` já existe desde o Lote 2 (`UserModel.funcionario_id`) — este lote só
cria a tabela que faltava (`funcionarios`, D196). **Não existe** `PATCH /employees/{id}` com um
campo `user_id`: a associação Funcionário↔Usuário é sempre feita do lado de `Usuário`
(`POST/PATCH /users` com `employee_id`, já implementado no Lote 2). `EmployeeModel` **não** ganha
uma coluna `usuario_id` — seria uma segunda origem da verdade para a mesma relação 1:1
(`relational/002-cadastros.md` já registra essa decisão explicitamente).

## Domain

```
modules/identity_access/domain/
├── value_objects/employee_status.py   # ATIVO / INATIVO (adicionado ao módulo já existente)
├── entities/employee.py               # Employee(BaseAggregateRoot[UUID])
└── repositories/employee_repository.py
```

`Employee.create(codigo, nome, cargo, data_admissao, audit)`. `Employee.update(...)`.
`Employee.deactivate(deactivated_by, now)`.

## Infrastructure

`EmployeeModel` — tabela `funcionarios`, adicionada a
`identity_access/infrastructure/persistence/models/identity_models.py` (mesmo arquivo dos outros
modelos do módulo, não um arquivo novo — `Employee` é pequeno o suficiente para não justificar
separação). `SqlAlchemyEmployeeRepository` — tenant-filtered (D338/D339).

## Application

`CreateEmployeeCommand`/`UpdateEmployeeCommand`/`DeactivateEmployeeCommand` +
`GetEmployeeQuery`/`ListEmployeesQuery`. Auditoria (D344) em create/deactivate, reusando
`core.audit.AuditLogger` como todo outro Command deste módulo desde o Lote 2 — nenhuma
implementação paralela.

`DeactivateEmployeeHandler` verifica se o Funcionário está vinculado a um Usuário `ATIVO`
(`UserRepository` já injetável dentro do mesmo módulo — nenhum import cross-module) antes de
completar a desativação, retornando `IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER` (422) se sim
(`010-employees.md`: "desativar um Funcionário ainda vinculado a um Usuário ATIVO exige desvincular
ou desativar o Usuário primeiro").

## Interfaces

`interfaces/api/employee_router.py` (novo arquivo, registrado em
`interfaces/api/v1/router.py` ao lado de `user_router`/`role_router`/`permission_router`) —
`GET/POST /employees`, `GET/PATCH/DELETE /employees/{id}`.

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `IDENTITY_EMPLOYEE_NOT_FOUND` | 404 | Funcionário não existe (ou outro tenant) |
| `IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER` | 422 | `DELETE` com Usuário `ATIVO` vinculado |

Sem `409` em `POST` — `funcionarios` não tem `UNIQUE` além de `(tenant_id, codigo)` gerado pela
aplicação (`010-employees.md`: nenhum CPF/documento único modelado para Funcionário — registrado
como observação da própria spec, não uma correção deste lote).

## Testes (D352)

- Unit: `Employee.create()`/`.deactivate()`.
- Integration: `SqlAlchemyEmployeeRepository` contra Postgres real — tenant isolation, soft delete.
- E2E: `POST /employees` → `GET` → `PATCH` → `DELETE` via HTTP real; caso adicional —
  `POST /employees` → `PATCH /users/{id}` com `employee_id` (vínculo, já existe desde o Lote 2) →
  `DELETE /employees/{id}` → `422 IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER`.
- Auditoria: `POST`/`DELETE /employees` geram `logs_auditoria`.
