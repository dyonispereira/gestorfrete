from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_contact_model import ClientContactModel
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverDocumentModel, DriverModel
from modules.financial.infrastructure.persistence.models.cost_center_model import CostCenterModel
from modules.identity_access.application.commands.create_role import CreateRoleCommand, CreateRoleHandler
from modules.identity_access.application.commands.create_user import CreateUserCommand, CreateUserHandler
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    EmployeeModel,
    PermissionModel,
    RoleModel,
    SessionModel,
    UserModel,
    papel_permissao,
    usuarios_papeis,
)
from modules.maintenance.infrastructure.persistence.models.supplier_model import SupplierModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared.addresses.infrastructure.persistence.models.address_model import AddressModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Exercises the Sprint 11 Lote 3 "Cadastros" surface — `crm` (Client/Contact), `maintenance`
(Supplier), `drivers` (Driver/Document), `identity_access` (Employee) and `financial` (CostCenter)
— plus the shared `Address` component, against the real Postgres schema end to end. Follows the
D352 Definition of Done: every scenario here proves (1) the migration applied cleanly (implicit —
these tables didn't exist before this suite could run), (2) the repository layer against a real
database, (3) the domain/application logic, (4) a real HTTP round-trip, and (5) tenant isolation/
audit for at least one representative aggregate each.
"""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("crm.client.view", "Ver clientes", "crm"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("crm.client.edit", "Editar clientes", "crm"),
    ("crm.client.delete", "Excluir clientes", "crm"),
    ("crm.client_contact.view", "Ver contatos", "crm"),
    ("crm.client_contact.create", "Criar contatos", "crm"),
    ("crm.client_contact.edit", "Editar contatos", "crm"),
    ("crm.client_contact.delete", "Excluir contatos", "crm"),
    ("maintenance.supplier.view", "Ver fornecedores", "maintenance"),
    ("maintenance.supplier.create", "Criar fornecedores", "maintenance"),
    ("maintenance.supplier.edit", "Editar fornecedores", "maintenance"),
    ("maintenance.supplier.delete", "Excluir fornecedores", "maintenance"),
    ("drivers.driver.view", "Ver motoristas", "drivers"),
    ("drivers.driver.view_own", "Ver o próprio cadastro", "drivers"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("drivers.driver.edit", "Editar motoristas", "drivers"),
    ("drivers.driver.delete", "Excluir motoristas", "drivers"),
    ("drivers.driver.block", "Bloquear motorista", "drivers"),
    ("drivers.driver.unblock", "Desbloquear motorista", "drivers"),
    ("identity_access.employee.view", "Ver funcionários", "identity_access"),
    ("identity_access.employee.create", "Criar funcionários", "identity_access"),
    ("identity_access.employee.edit", "Editar funcionários", "identity_access"),
    ("identity_access.employee.delete", "Excluir funcionários", "identity_access"),
    ("financial.cost_center.view", "Ver centros de custo", "financial"),
    ("financial.cost_center.create", "Criar centros de custo", "financial"),
    ("financial.cost_center.edit", "Editar centros de custo", "financial"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]


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


async def _full_access_actor(client: AsyncClient, tenants: list[uuid.UUID]) -> tuple[dict[str, str], uuid.UUID]:
    """Common setup for tests that don't care about RBAC granularity — one tenant, one role with
    every Cadastros permission, one logged-in user. Returns (headers, tenant_id)."""

    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    _, headers = await _login(client, email)
    return headers, tenant_id


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))).scalars().all()
        role_ids = (await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))).scalars().all()
        driver_ids = (
            await session.execute(select(DriverModel.id).where(DriverModel.tenant_id == tenant_id))
        ).scalars().all()
        client_ids = (
            await session.execute(select(ClientModel.id).where(ClientModel.tenant_id == tenant_id))
        ).scalars().all()

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))
        if driver_ids:
            await session.execute(delete(DriverDocumentModel).where(DriverDocumentModel.motorista_id.in_(driver_ids)))
        if client_ids:
            await session.execute(delete(ClientContactModel).where(ClientContactModel.cliente_id.in_(client_ids)))
        await session.execute(delete(AddressModel).where(AddressModel.tenant_id == tenant_id))
        await session.execute(delete(EmployeeModel).where(EmployeeModel.tenant_id == tenant_id))
        await session.execute(delete(CostCenterModel).where(CostCenterModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
        await session.execute(delete(SupplierModel).where(SupplierModel.tenant_id == tenant_id))
        await session.execute(delete(ClientModel).where(ClientModel.tenant_id == tenant_id))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


@pytest.fixture
async def permission_ids() -> dict[str, uuid.UUID]:
    return await _seed_permissions()


@pytest.fixture
async def tenants() -> AsyncIterator[list[uuid.UUID]]:
    created: list[uuid.UUID] = []
    yield created
    for tenant_id in created:
        await _cleanup_tenant(tenant_id)


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test() -> AsyncIterator[None]:
    """See `test_identity_access_flow.py` — pytest-asyncio gives each test its own event loop, but
    `get_engine()` is process-wide `lru_cache`d; disposing after every test avoids a pooled
    connection from one test's loop crashing the next test. Same reasoning applies to the Redis
    client (V1 Operational Hardening, Parte 6, `core/idempotency/`) — see `reset_redis_client`."""

    yield
    from core.cache.redis_client import reset_redis_client
    from core.database.session import dispose_engine

    await dispose_engine()
    await reset_redis_client()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from core.security.session_validation import reset_session_validator
    from main import create_app

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
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


class TestClientFlow:
    async def test_client_contact_and_address_full_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/clients",
            headers=headers,
            json={"razao_social": "Cliente Teste LTDA", "document": f"{uuid.uuid4().int % 10**11:011d}"},
        )
        assert create.status_code == 201, create.text
        client_id = create.json()["id"]

        get_resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "ATIVO"

        patch_resp = await client.patch(
            f"/api/v1/clients/{client_id}", headers=headers, json={"nome_fantasia": "Apelido"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["nome_fantasia"] == "Apelido"

        list_resp = await client.get("/api/v1/clients", headers=headers)
        assert list_resp.status_code == 200
        assert any(c["id"] == client_id for c in list_resp.json()["data"])

        contact_resp = await client.post(
            f"/api/v1/clients/{client_id}/contacts", headers=headers, json={"nome": "Fulano de Tal"}
        )
        assert contact_resp.status_code == 201, contact_resp.text
        contact_id = contact_resp.json()["id"]
        assert (await client.get(f"/api/v1/clients/{client_id}/contacts", headers=headers)).status_code == 200

        address_resp = await client.post(
            f"/api/v1/clients/{client_id}/addresses",
            headers=headers,
            json={
                "type": "PRINCIPAL",
                "logradouro": "Rua das Flores",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP",
                "cep": "01000-000",
            },
        )
        assert address_resp.status_code == 201, address_resp.text
        address_id = address_resp.json()["id"]

        # Um segundo endereço PRINCIPAL para o mesmo dono deve ser rejeitado pelo índice único
        # parcial físico (não uma checagem em memória) — prova D354's invariante real.
        duplicate_principal = await client.post(
            f"/api/v1/clients/{client_id}/addresses",
            headers=headers,
            json={
                "type": "PRINCIPAL",
                "logradouro": "Outra Rua",
                "bairro": "Outro Bairro",
                "cidade": "São Paulo",
                "uf": "SP",
                "cep": "02000-000",
            },
        )
        assert duplicate_principal.status_code == 409
        assert duplicate_principal.json()["error"]["code"] == "ADDRESS_PRINCIPAL_ALREADY_EXISTS"

        assert (await client.get(f"/api/v1/clients/{client_id}/addresses", headers=headers)).status_code == 200

        delete_contact = await client.delete(f"/api/v1/clients/{client_id}/contacts/{contact_id}", headers=headers)
        assert delete_contact.status_code == 204
        delete_address = await client.delete(f"/api/v1/clients/{client_id}/addresses/{address_id}", headers=headers)
        assert delete_address.status_code == 204

        deactivate = await client.delete(f"/api/v1/clients/{client_id}", headers=headers)
        assert deactivate.status_code == 204
        # D343 — soft delete é padrão de leitura: um Cliente desativado desaparece de consultas
        # normais (nunca um 200 com status INATIVO retornado de volta).
        after = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
        assert after.status_code == 404

        creation_logs = await _logs_for(tenant_id, "clientes", "CRIACAO")
        assert uuid.UUID(client_id) in creation_logs
        deactivation_logs = await _logs_for(tenant_id, "clientes", "EXCLUSAO_LOGICA")
        assert uuid.UUID(client_id) in deactivation_logs

    async def test_duplicate_document_returns_409(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)
        document = f"{uuid.uuid4().int % 10**11:011d}"

        first = await client.post(
            "/api/v1/clients", headers=headers, json={"razao_social": "A", "document": document}
        )
        assert first.status_code == 201

        second = await client.post(
            "/api/v1/clients", headers=headers, json={"razao_social": "B", "document": document}
        )
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "CRM_CLIENT_DOCUMENT_ALREADY_EXISTS"

    async def test_tenant_isolation_for_clients(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _ = await _full_access_actor(client, tenants)
        headers_b, _ = await _full_access_actor(client, tenants)

        created = await client.post(
            "/api/v1/clients",
            headers=headers_b,
            json={"razao_social": "Cliente do Tenant B", "document": f"{uuid.uuid4().int % 10**11:011d}"},
        )
        assert created.status_code == 201
        client_id = created.json()["id"]

        cross_tenant = await client.get(f"/api/v1/clients/{client_id}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "CRM_CLIENT_NOT_FOUND"


class TestSupplierFlow:
    async def test_supplier_and_address_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/suppliers",
            headers=headers,
            json={"razao_social": "Oficina Teste", "cnpj": f"{uuid.uuid4().int % 10**14:014d}", "category": "OFICINA"},
        )
        assert create.status_code == 201, create.text
        supplier_id = create.json()["id"]
        assert create.json()["category"] == "OFICINA"

        address_resp = await client.post(
            f"/api/v1/suppliers/{supplier_id}/addresses",
            headers=headers,
            json={
                "type": "PRINCIPAL",
                "logradouro": "Av. Industrial",
                "bairro": "Distrito",
                "cidade": "Campinas",
                "uf": "SP",
                "cep": "13000-000",
            },
        )
        assert address_resp.status_code == 201, address_resp.text

        patch_resp = await client.patch(
            f"/api/v1/suppliers/{supplier_id}", headers=headers, json={"telefone": "11999999999"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["telefone"] == "11999999999"

        deactivate = await client.delete(f"/api/v1/suppliers/{supplier_id}", headers=headers)
        assert deactivate.status_code == 204


class TestDriverFlow:
    async def test_driver_block_unblock_and_documents(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/drivers",
            headers=headers,
            json={"nome": "Motorista Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
        )
        assert create.status_code == 201, create.text
        driver_id = create.json()["id"]
        assert create.json()["fitness_status"] == "APTO"

        block = await client.post(f"/api/v1/drivers/{driver_id}/block", headers=headers)
        assert block.status_code == 200
        assert block.json()["fitness_status"] == "BLOQUEADO"

        block_again = await client.post(f"/api/v1/drivers/{driver_id}/block", headers=headers)
        assert block_again.status_code == 422
        assert block_again.json()["error"]["code"] == "DRIVERS_ALREADY_BLOCKED"

        unblock = await client.post(f"/api/v1/drivers/{driver_id}/unblock", headers=headers)
        assert unblock.status_code == 200
        assert unblock.json()["fitness_status"] == "APTO"

        cnh = await client.post(
            f"/api/v1/drivers/{driver_id}/documents",
            headers=headers,
            json={"type": "CNH", "number": "123456789", "cnh_category": "E", "expires_at": "2099-01-01"},
        )
        assert cnh.status_code == 201, cnh.text
        assert cnh.json()["status"] == "VALIDO"

        invalid_category = await client.post(
            f"/api/v1/drivers/{driver_id}/documents",
            headers=headers,
            json={"type": "RG", "number": "MG-1234", "cnh_category": "B"},
        )
        assert invalid_category.status_code == 422
        assert invalid_category.json()["error"]["code"] == "DRIVERS_CNH_CATEGORY_REQUIRES_CNH_TYPE"

        expired = await client.post(
            f"/api/v1/drivers/{driver_id}/documents",
            headers=headers,
            json={"type": "EXAME_TOXICOLOGICO", "number": "EX-1", "expires_at": str(date(2000, 1, 1))},
        )
        assert expired.status_code == 201
        assert expired.json()["status"] == "VENCIDO"

        documents = await client.get(f"/api/v1/drivers/{driver_id}/documents", headers=headers)
        assert documents.status_code == 200
        assert documents.json()["meta"]["pagination"]["total"] == 2

        deactivate = await client.delete(f"/api/v1/drivers/{driver_id}", headers=headers)
        assert deactivate.status_code == 204

    async def test_get_my_driver_requires_a_linked_user(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)

        not_a_driver = await client.get("/api/v1/drivers/me", headers=headers)
        assert not_a_driver.status_code == 404
        assert not_a_driver.json()["error"]["code"] == "DRIVERS_NOT_A_DRIVER_ACCOUNT"


class TestEmployeeFlow:
    async def test_employee_lifecycle_and_active_user_link_blocks_deactivation(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/employees", headers=headers, json={"nome": "Funcionário Teste", "cargo": "Mecânico"}
        )
        assert create.status_code == 201, create.text
        employee_id = create.json()["id"]

        patch_resp = await client.patch(
            f"/api/v1/employees/{employee_id}", headers=headers, json={"cargo": "Mecânico Chefe"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["cargo"] == "Mecânico Chefe"

        # `PATCH /users` ainda não expõe `employee_id` (gap pré-existente do Lote 2, fora de escopo
        # deste lote) — o vínculo é simulado diretamente no banco para provar a regra de negócio
        # real de `DeactivateEmployeeHandler` (usuarios.funcionario_id + status ATIVO).
        token = set_current_tenant_id(tenant_id)
        try:
            role_id = await _create_role(tenant_id, ["identity_access.employee.view"])
            linked_user_id, _ = await _create_user(tenant_id, role_ids=frozenset({role_id}))
            session_factory = get_session_factory()
            async with session_factory() as session:
                user_model = await session.get(UserModel, linked_user_id)
                assert user_model is not None
                user_model.funcionario_id = uuid.UUID(employee_id)
                await session.commit()
        finally:
            reset_current_tenant_id(token)

        blocked_delete = await client.delete(f"/api/v1/employees/{employee_id}", headers=headers)
        assert blocked_delete.status_code == 422
        assert blocked_delete.json()["error"]["code"] == "IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER"

        creation_logs = await _logs_for(tenant_id, "funcionarios", "CRIACAO")
        assert uuid.UUID(employee_id) in creation_logs


class TestCostCenterFlow:
    async def test_cost_center_lifecycle_has_no_delete_endpoint(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/cost-centers",
            headers=headers,
            json={"accounting_code": f"CC-{uuid.uuid4().hex[:8]}", "nome": "Centro de Custo Teste"},
        )
        assert create.status_code == 201, create.text
        cost_center_id = create.json()["id"]
        assert create.json()["branch_id"] is None

        # `filial_id` é aceito mesmo sem FK física ainda (D355) — confirma que a ausência da
        # constraint não quebra a escrita.
        random_branch_id = str(uuid.uuid4())
        patch_resp = await client.patch(
            f"/api/v1/cost-centers/{cost_center_id}",
            headers=headers,
            json={"branch_id": random_branch_id, "status": "INATIVO"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["branch_id"] == random_branch_id
        assert patch_resp.json()["status"] == "INATIVO"

        no_delete = await client.delete(f"/api/v1/cost-centers/{cost_center_id}", headers=headers)
        assert no_delete.status_code == 405

    async def test_duplicate_accounting_code_returns_409(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)
        code = f"CC-{uuid.uuid4().hex[:8]}"

        first = await client.post("/api/v1/cost-centers", headers=headers, json={"accounting_code": code, "nome": "A"})
        assert first.status_code == 201

        second = await client.post("/api/v1/cost-centers", headers=headers, json={"accounting_code": code, "nome": "B"})
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "FINANCIAL_COST_CENTER_CODE_ALREADY_EXISTS"
