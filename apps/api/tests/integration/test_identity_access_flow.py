from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.identity_access.application.commands.create_role import CreateRoleCommand, CreateRoleHandler
from modules.identity_access.application.commands.create_user import CreateUserCommand, CreateUserHandler
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    PermissionModel,
    RoleModel,
    SessionModel,
    UserModel,
    papel_permissao,
    usuarios_papeis,
)
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Exercises `modules.tenancy`/`modules.identity_access` against the real, Alembic-migrated
PostgreSQL schema — RBAC/tenant isolation/soft delete/session revocation all depend on real
constraints and real cross-table queries, not assumptions a mock could hide. Requires
``DATABASE_URL`` to point at a reachable Postgres (the portable instance on port 5433 for local
dev, or the ``docker compose`` ``postgres`` service) — run with ``pytest -m integration``.

Uses ``httpx.AsyncClient`` over ``ASGITransport`` rather than ``fastapi.testclient.TestClient``:
the latter drives the ASGI app from its own background event loop, which collides with the
process-wide, ``lru_cache``d asyncpg pool (``core.database.session.get_engine``) the moment a test
also awaits the repository layer directly in the same function — the pool ends up straddling two
loops and asyncpg raises ``RuntimeError: ... attached to a different loop``. ``AsyncClient`` runs
the whole request inside the *same* loop as the test coroutine, so there is only ever one loop.
"""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("identity_access.user.view", "Ver usuários", "identity_access"),
    ("identity_access.role.view", "Ver papéis", "identity_access"),
    ("tenancy.company_data.view", "Ver dados do tenant", "tenancy"),
]
"""Subconjunto real de `permissoes` — o catálogo completo (RBAC_MATRIX.md) ainda não tem um seed
de produção (nenhum lote pediu isso até aqui); estas linhas são inseridas via `get_or_create` e
persistem como Platform Reference Data real, nunca apagadas no teardown do teste."""


async def _seed_permissions() -> dict[str, uuid.UUID]:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    ids: dict[str, uuid.UUID] = {}
    async with session_factory() as session:
        for codigo, nome, modulo in PERMISSION_CATALOG:
            existing = (
                await session.execute(select(PermissionModel).where(PermissionModel.codigo == codigo))
            ).scalar_one_or_none()
            if existing is None:
                model = PermissionModel(id=uuid.uuid4(), codigo=codigo, nome=nome, modulo=modulo, criado_em=now)
                session.add(model)
                await session.flush()
                ids[codigo] = model.id
            else:
                ids[codigo] = existing.id
        await session.commit()
    return ids


async def _create_tenant() -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    tenant_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=tenant_id,
                codigo=f"T-{tenant_id.hex[:8]}",
                versao=1,
                razao_social="Transportadora de Teste LTDA",
                cnpj=f"{tenant_id.int % 10**14:014d}",
                status="ATIVO",
                criado_em=now,
                atualizado_em=now,
            )
        )
        await session.commit()
    return tenant_id


async def _create_role(tenant_id: uuid.UUID, permission_codes: list[str]) -> uuid.UUID:
    """Uses a synthetic, never-persisted-as-a-user "bootstrap actor" purely to satisfy
    `CreateRoleCommand.actor` (audit trail fields) — there is no seed/bootstrap endpoint yet
    (out of scope for this lote), so integration tests drive the real Application layer directly,
    exactly like a first-run provisioning script would."""

    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateRoleHandler().handle(
            CreateRoleCommand(
                actor=bootstrap_actor,
                nome=f"Papel-{uuid.uuid4().hex[:8]}",
                descricao=None,
                permission_codes=permission_codes,
            )
        )
        return dto.id
    finally:
        reset_current_tenant_id(token)


async def _create_user(tenant_id: uuid.UUID, *, role_ids: frozenset[uuid.UUID]) -> tuple[uuid.UUID, str]:
    email = f"user-{uuid.uuid4().hex[:10]}@teste.com"
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateUserHandler().handle(
            CreateUserCommand(
                actor=bootstrap_actor,
                nome="Usuário de Teste",
                email=email,
                password=PASSWORD,
                driver_id=None,
                employee_id=None,
                role_ids=role_ids,
            )
        )
        return dto.id, email
    finally:
        reset_current_tenant_id(token)


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (
            await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))
        ).scalars().all()
        role_ids = (
            await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))
        ).scalars().all()
        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


@pytest.fixture
async def permission_ids() -> dict[str, uuid.UUID]:
    return await _seed_permissions()


@pytest.fixture
async def tenants() -> AsyncIterator[list[uuid.UUID]]:
    """Collects every tenant a test creates so it can be torn down afterwards — real rows in the
    real database, never rolled back implicitly (each command owns and commits its own
    transaction, so there is nothing to roll back)."""

    created: list[uuid.UUID] = []
    yield created
    for tenant_id in created:
        await _cleanup_tenant(tenant_id)


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test() -> AsyncIterator[None]:
    """``core.database.session.get_engine`` is process-wide ``lru_cache``d, but pytest-asyncio
    hands each test function its own event loop — a pooled asyncpg connection created under one
    test's loop crashes if reused under the next test's (now-closed) loop. Disposing after every
    test forces the next one to lazily build a brand-new pool bound to its own loop."""

    yield
    from core.database.session import dispose_engine

    await dispose_engine()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from core.security.session_validation import reset_session_validator
    from main import create_app

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        # create_app() wires the real SqlAlchemySessionValidator globally (core.security.
        # session_validation has no per-test scoping) — undone here so other test files that
        # build their own minimal app (e.g. tests/unit/test_auth_dependency.py) keep seeing the
        # default always-valid null validator, matching their own fixtures/expectations.
        reset_session_validator()


async def _login(client: AsyncClient, email: str) -> tuple[str, dict[str, str]]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


async def _logs_for(tenant_id: uuid.UUID, entidade_tipo: str, acao: str) -> list[uuid.UUID]:
    from core.audit.models import LogAuditoriaModel

    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(LogAuditoriaModel.entidade_id).where(
                    LogAuditoriaModel.tenant_id == tenant_id,
                    LogAuditoriaModel.entidade_tipo == entidade_tipo,
                    LogAuditoriaModel.acao == acao,
                )
            )
        ).scalars().all()
    return list(rows)


class TestTenantIsolation:
    async def test_user_from_tenant_a_cannot_read_user_from_tenant_b(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_a, tenant_b = await _create_tenant(), await _create_tenant()
        tenants.extend([tenant_a, tenant_b])

        role_a = await _create_role(tenant_a, ["identity_access.user.view"])
        user_a_id, email_a = await _create_user(tenant_a, role_ids=frozenset({role_a}))

        role_b = await _create_role(tenant_b, ["identity_access.user.view"])
        user_b_id, _email_b = await _create_user(tenant_b, role_ids=frozenset({role_b}))

        _, headers_a = await _login(client, email_a)

        own_response = await client.get(f"/api/v1/users/{user_a_id}", headers=headers_a)
        assert own_response.status_code == 200

        cross_tenant_response = await client.get(f"/api/v1/users/{user_b_id}", headers=headers_a)
        assert cross_tenant_response.status_code == 404
        assert cross_tenant_response.json()["error"]["code"] == "IDENTITY_USER_NOT_FOUND"


class TestRbac:
    async def test_user_without_permission_gets_403(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role = await _create_role(tenant_id, ["tenancy.company_data.view"])  # no user.view
        _, email = await _create_user(tenant_id, role_ids=frozenset({role}))

        _, headers = await _login(client, email)
        response = await client.get("/api/v1/users", headers=headers)

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "IDENTITY_PERMISSION_DENIED"

    async def test_single_role_only_grants_its_own_permissions(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role = await _create_role(tenant_id, ["identity_access.role.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role}))

        _, headers = await _login(client, email)

        allowed = await client.get("/api/v1/roles", headers=headers)
        assert allowed.status_code == 200

        denied = await client.get("/api/v1/users", headers=headers)
        assert denied.status_code == 403

    async def test_multiple_roles_grant_the_union_of_permissions(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role_users = await _create_role(tenant_id, ["identity_access.user.view"])
        role_roles = await _create_role(tenant_id, ["identity_access.role.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_users, role_roles}))

        _, headers = await _login(client, email)

        assert (await client.get("/api/v1/users", headers=headers)).status_code == 200
        assert (await client.get("/api/v1/roles", headers=headers)).status_code == 200


class TestSoftDelete:
    async def test_deactivated_user_is_excluded_from_normal_queries_but_row_still_exists(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role = await _create_role(tenant_id, ["identity_access.user.view"])
        target_id, _ = await _create_user(tenant_id, role_ids=frozenset({role}))

        # Soft-deletes directly through the domain entity (same path DeactivateUserHandler takes)
        # to isolate this assertion from the RBAC/permission concerns already covered above.
        from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
            SqlAlchemyUserRepository,
        )

        token = set_current_tenant_id(tenant_id)
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                repo = SqlAlchemyUserRepository(session)
                user = await repo.get_by_id(target_id)
                assert user is not None
                user.deactivate(deactivated_by=uuid.uuid4(), now=datetime.now(timezone.utc))
                await repo.add(user)
                await session.commit()

            async with session_factory() as session:
                repo = SqlAlchemyUserRepository(session)
                assert await repo.get_by_id(target_id) is None
        finally:
            reset_current_tenant_id(token)

        async with get_session_factory()() as session:
            row = await session.get(UserModel, target_id)
            assert row is not None
            assert row.excluido_em is not None
            assert row.status == "INATIVO"


class TestSessionRevocation:
    async def test_logout_revokes_session_even_with_a_still_valid_looking_jwt(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role = await _create_role(tenant_id, ["identity_access.user.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role}))

        _token, headers = await _login(client, email)

        before_logout = await client.get("/api/v1/auth/me", headers=headers)
        assert before_logout.status_code == 200

        logout_response = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 204

        after_logout = await client.get("/api/v1/auth/me", headers=headers)
        assert after_logout.status_code == 401
        assert after_logout.json()["error"]["code"] == "IDENTITY_SESSION_REVOKED"


class TestJwtValidation:
    async def test_expired_token_is_rejected(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role = await _create_role(tenant_id, ["identity_access.user.view"])
        user_id, _email = await _create_user(tenant_id, role_ids=frozenset({role}))

        import jose.jwt as jose_jwt

        from core.config.settings import get_settings

        settings = get_settings()
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "session_id": str(uuid.uuid4()),
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=1),
        }
        expired_token = jose_jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "IDENTITY_TOKEN_EXPIRED"

    async def test_invalid_token_is_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "IDENTITY_INVALID_CREDENTIALS"


class TestAudit:
    async def test_critical_identity_operations_produce_audit_log_rows(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role_id = await _create_role(tenant_id, ["identity_access.user.view"])
        user_id, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))

        role_logs = await _logs_for(tenant_id, "papeis", "CRIACAO")
        assert role_id in role_logs

        user_logs = await _logs_for(tenant_id, "usuarios", "CRIACAO")
        assert user_id in user_logs

        _, headers = await _login(client, email)
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        session_id = uuid.UUID(me_response.json()["session"]["id"])

        login_logs = await _logs_for(tenant_id, "sessoes_acesso", "LOGIN")
        assert session_id in login_logs

        await client.post("/api/v1/auth/logout", headers=headers)
        logout_logs = await _logs_for(tenant_id, "sessoes_acesso", "LOGOUT")
        assert session_id in logout_logs


class TestEndToEndFlow:
    async def test_login_to_protected_endpoint_full_chain(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        """The exact chain the user asked to see proven end to end: POST /auth/login -> JWT ->
        GET /auth/me -> Tenant/Role/Permission resolved -> a protected endpoint gated by RBAC."""

        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        role_id = await _create_role(tenant_id, ["identity_access.user.view", "tenancy.company_data.view"])
        user_id, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))

        token, headers = await _login(client, email)
        assert token

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        body = me.json()
        assert body["user"]["id"] == str(user_id)
        assert body["tenant"]["id"] == str(tenant_id)
        assert body["roles"]

        tenant_response = await client.get("/api/v1/tenant", headers=headers)
        assert tenant_response.status_code == 200
        assert tenant_response.json()["id"] == str(tenant_id)

        users_response = await client.get("/api/v1/users", headers=headers)
        assert users_response.status_code == 200
        assert any(item["id"] == str(user_id) for item in users_response.json()["data"])
