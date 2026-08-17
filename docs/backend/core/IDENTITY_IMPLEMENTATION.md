# IDENTITY_IMPLEMENTATION.md — Como o contrato de Usuário/Papel/Permissão vira código

Bounded context `identity_access` (`modules/identity_access/`). Traduz `docs/api/003-users.md`,
`004-roles.md`, `005-permissions.md` (todos congelados).

## Três Aggregate Roots, uma relação N:N entre dois deles

```
Usuário ──(usuarios_papeis, N:N)── Papel ──(papel_permissao, N:N)── Permissão
```

`Permissão` é **Platform Reference Data** (D046) — sem `tenant_id`, sem escrita nesta API
(`005-permissions.md`: "somente leitura para clientes normais"). `Usuário` e `Papel` são Aggregate
Roots plenos, cada um dono da sua própria junção (`usuarios_papeis`/`papel_permissao` nunca são
Aggregate Roots próprios — são detalhe de persistência de `Usuário`/`Papel`, nunca expostos como
recurso HTTP independente).

## `domain/entities/user.py`

```python
class User(BaseAggregateRoot[uuid.UUID]):
    codigo: str
    nome: str
    email: str
    senha_hash: str                  # nunca serializado para fora do domain — sem __repr__ que o exponha
    status: UserStatus               # ATIVO/INATIVO/BLOQUEADO
    driver_id: uuid.UUID | None       # XOR com employee_id (ck_usuarios_motorista_xor_funcionario)
    employee_id: uuid.UUID | None
    role_ids: frozenset[uuid.UUID]    # espelha usuarios_papeis — nunca a lista de Role completa
    audit: AuditMetadata

    @classmethod
    def create(cls, *, nome, email, password_hash, driver_id, employee_id, role_ids) -> "User":
        if driver_id and employee_id:
            raise DomainRuleViolationError(
                "IDENTITY_USER_DRIVER_AND_EMPLOYEE_CONFLICT",
                "Usuário não pode estar vinculado a Motorista e Funcionário ao mesmo tempo.",
            )
        user = cls(id=uuid.uuid4(), ...)
        user.record_event(UsuarioCriado(...))
        return user

    def replace_roles(self, role_ids: frozenset[uuid.UUID]) -> None:
        """`role_ids` é sempre o conjunto final, nunca incremental (003-users.md, mesma regra do
        contrato) — `usuarios_papeis` é recalculado para bater exatamente com este conjunto."""
        if role_ids != self.role_ids:
            self.role_ids = role_ids
            self.record_event(PapeisDoUsuarioAlterados(...))   # dispara Auditoria, D344

    def deactivate(self) -> None:
        if self.status == UserStatus.INATIVO:
            raise ConflictError("IDENTITY_USER_ALREADY_INACTIVE", "...")
        self.status = UserStatus.INATIVO
        self.record_event(UsuarioDesativado(...))
```

`role_ids` fica no próprio agregado `User` (não um agregado `UsuarioPapeis` separado) — decisão de
modelagem: a PK de `usuarios_papeis` já é `(usuario_id, papel_id)` liderada por `usuario_id`
(`relational/001-core.md`, "a consulta mais frequente é 'quais Papéis este Usuário tem'"), então o
agregado natural que controla essa junção é `User`, nunca `Role`.

## `application/commands/` — `CreateUser`, `UpdateUser`, `SoftDeleteUser`

```python
class CreateUserHandler(CommandHandler[CreateUserCommand, User]):
    async def handle(self, command: CreateUserCommand) -> User:
        await authorize(command.actor, "identity_access.user.create")   # AUTHORIZATION_IMPLEMENTATION.md
        async with SQLAlchemyUnitOfWork() as uow:
            user_repo, role_repo = ...
            if await user_repo.exists_with_email(command.email):
                raise ConflictError("IDENTITY_EMAIL_ALREADY_EXISTS", "...")
            roles = await role_repo.get_many(command.role_ids)   # 404 se algum id não existir/for de outro tenant
            user = User.create(..., password_hash=self._hasher.hash(command.password))
            await user_repo.add(user)
            await uow.commit()
            await self._publish_events(user)   # TRANSACTION_MODEL.md — só depois do commit
            await self._audit.record("usuarios", user.id, "CRIACAO", actor=command.actor)  # D344
            return user
```

`SoftDeleteUserHandler` — **regra de negócio explícita do contrato** (`003-users.md`, `422
IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN`): antes de desativar, conta quantos outros Usuários `ATIVO`
do tenant têm um Papel que inclua `identity_access.role.*` (Administrador) — não uma `CHECK` física
(a contagem depende de RBAC resolvido, não é um invariante que o banco consiga expressar sozinho,
mesmo princípio de `CONSTRAINTS.md`'s "Camada Responsável").

## `application/commands/` — Papel (`Role`)

CRUD completo (`004-roles.md`) + `permissions: list[str]` — cada código validado contra o catálogo
real de `Permissão` antes de gravar `papel_permissao` (nunca um código inventado on-the-fly, D216
aplicado agora em runtime, não só em documentação):

```python
async def _resolve_permission_ids(self, codes: list[str]) -> list[uuid.UUID]:
    permissions = await self._permission_repo.get_by_codes(codes)
    found_codes = {p.code for p in permissions}
    unknown = set(codes) - found_codes
    if unknown:
        raise ValidationError("IDENTITY_UNKNOWN_PERMISSION_CODE", f"Códigos inexistentes: {unknown}")
    return [p.id for p in permissions]
```

`DeleteRoleHandler` — `422 IDENTITY_ROLE_IN_USE` se `usuarios_papeis` ainda referenciar o papel
(checado antes do soft delete, nunca deixando um Usuário referenciando um Papel excluído
silenciosamente).

## `application/queries/` — Permissão (`Permission`)

`ListPermissionsHandler`/`GetPermissionHandler` — só leitura, direto do catálogo (`permissoes`, sem
`tenant_id`, mesma query para qualquer tenant). Nenhum `CommandHandler` existe para Permissão nesta
API — coerente com `005-permissions.md`.

## `infrastructure/persistence/models/`

`UserModel`/`RoleModel`/`PermissionModel` + as duas tabelas de junção mapeadas como
`relationship(secondary=...)` do SQLAlchemy (nunca como Aggregate Roots próprios). `PermissionModel`
é a única sem `tenant_id` — `SqlAlchemyPermissionRepository` nunca filtra por tenant (D046 aplicado
até a query).

## Testes obrigatórios deste bounded context

- Criar Usuário com `driver_id` **e** `employee_id` preenchidos: `422`.
- `PATCH /users/{id}` com `role_ids: ["A"]` quando o usuário tinha `["A","B"]` remove `B` de
  `usuarios_papeis` (substituição completa, não incremental).
- `DELETE` do último Usuário Administrador do tenant: `422 IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN`.
- `POST /roles` com um código de permissão inexistente: `400 IDENTITY_UNKNOWN_PERMISSION_CODE`,
  nenhuma linha gravada (transação inteira revertida, `TRANSACTION_MODEL.md`).
- `DELETE /roles/{id}` de um Papel ainda em uso: `422 IDENTITY_ROLE_IN_USE`.
- `GET /permissions` nunca filtra por tenant — mesmo resultado para dois tenants diferentes.
- Usuário com dois Papéis recebe a **união** das permissões dos dois (ver
  [`AUTHORIZATION_IMPLEMENTATION.md`](./AUTHORIZATION_IMPLEMENTATION.md)).
