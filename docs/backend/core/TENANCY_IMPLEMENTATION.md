# TENANCY_IMPLEMENTATION.md — Como o contrato de Tenant vira código

Bounded context `tenancy` (`modules/tenancy/`). Traduz `docs/api/002-tenants.md` (congelado) para
Domain/Application/Infrastructure/Interfaces — não repete o contrato, só como ele é implementado.

## Escopo deste lote

**Só** `GET`/`PATCH /api/v1/tenant` — exatamente o que `002-tenants.md` já congela. Nenhuma criação
de Tenant (isso é `onboarding`, ainda sem endpoint, `OPENAPI_FREEZE.md` lacuna #1) e nenhum
`GET /tenants` em lista (o contrato é deliberadamente singular — "o" tenant do contexto
autenticado).

## `domain/entities/tenant.py`

```python
class Tenant(BaseAggregateRoot[uuid.UUID]):
    codigo: str
    versao: int
    razao_social: str
    cnpj: str
    status: TenantStatus            # enum: TRIAL/ATIVO/SUSPENSO/CANCELADO — readOnly na API
    audit: AuditMetadata            # shared_kernel — criado_em/por, atualizado_em/por

    def update_company_data(self, razao_social: str | None, cnpj: str | None) -> None:
        """Único método de escrita do agregado nesta etapa — status nunca é alterado por aqui
        (governado pelo fluxo de assinatura/cobrança, D-alinhado a 002-tenants.md linha 46)."""
```

`status` nunca tem setter público — mesma disciplina de D233 (status não é mutável por CRUD, só por
comando) já aplicada em toda a OpenAPI; aqui simplesmente não existe nenhum comando de mudança de
status neste bounded context ainda (fica para quando `subscription`/`billing` forem implementados).

## `domain/repositories/tenant_repository.py`

```python
class TenantRepository(Repository[Tenant, uuid.UUID]):
    async def get_by_id(self, id: uuid.UUID) -> Tenant | None: ...
    async def add(self, aggregate: Tenant) -> None: ...     # nunca chamado neste lote (sem POST)
    async def find(self, specification) -> list[Tenant]: ...  # nunca chamado neste lote (sem lista)
```

Interface pura (porta) — sem `tenant_id` como parâmetro em nenhum método, mesma disciplina de
`DOMAIN_LAYER.md`. Para `Tenant` especificamente, `get_by_id` **é** o próprio tenant do contexto —
nunca usado para buscar um tenant arbitrário por ID vindo de fora (não existe rota que aceite um
`tenant_id` de path para este recurso).

## `application/queries/get_tenant.py` + `application/commands/update_tenant.py`

```python
@dataclass(frozen=True)
class GetTenantQuery(Query):
    actor: AuthenticatedActor

class GetTenantHandler(QueryHandler[GetTenantQuery, Tenant]):
    async def handle(self, query: GetTenantQuery) -> Tenant:
        tenant = await self._repo.get_by_id(query.actor.tenant_id)   # nunca outro id
        if tenant is None:
            raise InfrastructureError("TENANCY_CONTEXT_TENANT_MISSING", "...")  # nunca deveria acontecer
        return tenant

@dataclass(frozen=True)
class UpdateTenantCommand(Command):
    actor: AuthenticatedActor
    razao_social: str | None
    cnpj: str | None

class UpdateTenantHandler(CommandHandler[UpdateTenantCommand, Tenant]):
    async def handle(self, command: UpdateTenantCommand) -> Tenant:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTenantRepository(uow.session)
            tenant = await repo.get_by_id(command.actor.tenant_id)
            if tenant is None: raise NotFoundError(...)
            try:
                tenant.update_company_data(command.razao_social, command.cnpj)
            except DuplicateCnpjError:
                raise ConflictError("TENANCY_CNPJ_ALREADY_EXISTS", "...")
            await uow.commit()
            return tenant
```

**Regra crítica (D338/D339)**: `command.actor.tenant_id` — nunca um `tenant_id` recebido do corpo
da requisição. O schema Pydantic de `PATCH /tenant` (`interfaces/schemas/`) nem declara um campo
`tenant_id` — o corpo aceito é exatamente `{razao_social?, cnpj?}`, igual ao contrato. Se o cliente
mandar `tenant_id` mesmo assim, Pydantic o ignora silenciosamente (schema com `extra="ignore"`,
nunca `extra="allow"` para nenhum schema de entrada desta API).

## `infrastructure/persistence/models/tenant_model.py`

Mapeamento SQLAlchemy 1:1 com `tenants` (`relational/001-core.md`) — `id`/`codigo`/`versao`/
`razao_social`/`cnpj`/`status`/`criado_em`/`criado_por`/`atualizado_em`/`atualizado_por`/
`excluido_em`/`excluido_por`. `SqlAlchemyTenantRepository.get_by_id` sempre filtra
`WHERE excluido_em IS NULL` (D343) — nunca retorna um Tenant logicamente excluído (cenário
hipotético hoje, já que não existe comando de exclusão de Tenant nesta API, mas a regra é do
Repository, não do endpoint, então vale por construção).

## `interfaces/api/tenant_router.py`

```python
@router.get("/tenant", dependencies=[Depends(require_permission("tenancy.company_data.view"))])
async def get_tenant(actor: AuthenticatedActor = Depends(get_current_actor)) -> TenantResponse: ...

@router.patch("/tenant", dependencies=[Depends(require_permission("tenancy.company_data.edit"))])
async def update_tenant(
    body: UpdateTenantRequest, actor: AuthenticatedActor = Depends(get_current_actor)
) -> TenantResponse: ...
```

`require_permission(...)` — ver [`AUTHORIZATION_IMPLEMENTATION.md`](./AUTHORIZATION_IMPLEMENTATION.md).
Schemas de request/response espelham exatamente `002-tenants.md`/`components/schemas.md#Tenant` —
`status` é `readOnly` no `TenantResponse` (nunca aparece em `UpdateTenantRequest`).

## Testes obrigatórios deste bounded context

- `GET /tenant` retorna o tenant do actor autenticado, nunca outro.
- `PATCH /tenant` nunca aceita `status` nem `tenant_id` no corpo (campos extra ignorados, resultado
  inalterado nesses dois campos mesmo se enviados).
- `PATCH /tenant` com CNPJ duplicado retorna `409 TENANCY_CNPJ_ALREADY_EXISTS`.
- Sem `tenancy.company_data.edit`: `403`.
