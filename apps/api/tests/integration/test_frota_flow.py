from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.fleet.infrastructure.persistence.models.implement_model import ImplementModel
from modules.fleet.infrastructure.persistence.models.odometer_reading_model import OdometerReadingModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_composition_model import (
    VehicleCompositionModel,
    composicoes_veiculares_implementos,
)
from modules.fleet.infrastructure.persistence.models.vehicle_document_model import VehicleDocumentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.fleet.infrastructure.persistence.models.vehicle_technical_sheet_model import (
    VehicleTechnicalSheetModel,
)
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
"""Sprint 11, Lote 4 — Frota. D352 Definition of Done aplicado aos 5 agregados (`Vehicle`,
`Implement`, `VehicleComposition`, `OdometerReading`, `VehicleAvailability`) mais as duas
auditorias explicitamente pedidas pelo usuário: (1) `disponibilidade_veiculo` não tem nenhum
caminho de escrita HTTP; (2) nunca existem duas Composições Veiculares vigentes para o mesmo
veículo simultaneamente."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("fleet.vehicle.view", "Ver veículos", "fleet"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("fleet.vehicle.edit", "Editar veículos", "fleet"),
    ("fleet.vehicle.delete", "Excluir veículos", "fleet"),
    ("fleet.vehicle.view_availability", "Ver disponibilidade de veículos", "fleet"),
    ("fleet.vehicle_technical_sheet.view", "Ver ficha técnica", "fleet"),
    ("fleet.vehicle_technical_sheet.edit", "Editar ficha técnica", "fleet"),
    ("fleet.vehicle_document.view", "Ver documentos do veículo", "fleet"),
    ("fleet.vehicle_document.attach", "Anexar documento do veículo", "fleet"),
    ("fleet.implement.view", "Ver implementos", "fleet"),
    ("fleet.implement.create", "Criar implementos", "fleet"),
    ("fleet.implement.edit", "Editar implementos", "fleet"),
    ("fleet.implement.delete", "Excluir implementos", "fleet"),
    ("fleet.vehicle_composition.view", "Ver composições veiculares", "fleet"),
    ("fleet.vehicle_composition.create", "Criar composições veiculares", "fleet"),
    ("fleet.vehicle_composition.validate", "Validar composição veicular", "fleet"),
    ("fleet.odometer_reading.view", "Ver leituras de hodômetro", "fleet"),
    ("fleet.odometer_reading.create", "Registrar leitura de hodômetro", "fleet"),
    # `disponibilidade_veiculo.motorista_atual_id` tem FK real para `motoristas` — o teste da
    # projeção precisa de um Motorista real (Lote 3) para satisfazer a constraint.
    ("drivers.driver.create", "Criar motoristas", "drivers"),
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
                id=tenant_id, codigo=f"T-{tenant_id.hex[:8]}", versao=1, razao_social="Transportadora de Teste LTDA",
                cnpj=f"{tenant_id.int % 10**14:014d}", status="ATIVO", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return tenant_id


async def _seed_vehicle_category(tenant_id: uuid.UUID) -> uuid.UUID:
    """`Categoria de Veículo` não tem endpoint HTTP (D363) — seed direto via model, mesmo padrão
    de `permissoes` (Platform Reference Data)."""

    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    category_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            VehicleCategoryModel(
                id=category_id, tenant_id=tenant_id, codigo=f"CAT-{category_id.hex[:8]}", nome=f"Categoria {category_id.hex[:6]}",
                status="ATIVA", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return category_id


async def _create_role(tenant_id: uuid.UUID, permission_codes: list[str]) -> uuid.UUID:
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateRoleHandler().handle(
            CreateRoleCommand(actor=bootstrap_actor, nome=f"Papel-{uuid.uuid4().hex[:8]}", descricao=None, permission_codes=permission_codes)
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
                actor=bootstrap_actor, nome="Usuário de Teste", email=email, password=PASSWORD, driver_id=None,
                employee_id=None, role_ids=role_ids,
            )
        )
        return dto.id, email
    finally:
        reset_current_tenant_id(token)


async def _full_access_actor(client: AsyncClient, tenants: list[uuid.UUID]) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    """Retorna (headers, tenant_id, category_id)."""

    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    category_id = await _seed_vehicle_category(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    _, headers = await _login(client, email)
    return headers, tenant_id, category_id


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))).scalars().all()
        role_ids = (await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))).scalars().all()
        composition_ids = (
            await session.execute(select(VehicleCompositionModel.id).where(VehicleCompositionModel.tenant_id == tenant_id))
        ).scalars().all()

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))
        if composition_ids:
            await session.execute(
                delete(composicoes_veiculares_implementos).where(
                    composicoes_veiculares_implementos.c.composicao_veicular_id.in_(composition_ids)
                )
            )
        await session.execute(delete(VehicleCompositionModel).where(VehicleCompositionModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
        await session.execute(delete(OdometerReadingModel).where(OdometerReadingModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleDocumentModel).where(VehicleDocumentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleTechnicalSheetModel).where(VehicleTechnicalSheetModel.tenant_id == tenant_id))
        await session.execute(delete(ImplementModel).where(ImplementModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
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


def _plate(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"


class TestVehicleFlow:
    async def test_vehicle_technical_sheet_and_documents_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/veiculos",
            headers=headers,
            json={
                "plate": _plate("VEI"), "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Volvo",
                "modelo": "FH540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
            },
        )
        assert create.status_code == 201, create.text
        vehicle_id = create.json()["id"]

        get_resp = await client.get(f"/api/v1/veiculos/{vehicle_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "ATIVO"

        sheet_missing = await client.get(f"/api/v1/veiculos/{vehicle_id}/technical-sheet", headers=headers)
        assert sheet_missing.status_code == 404
        assert sheet_missing.json()["error"]["code"] == "FLEET_VEHICLE_TECHNICAL_SHEET_NOT_FOUND"

        sheet_resp = await client.patch(
            f"/api/v1/veiculos/{vehicle_id}/technical-sheet",
            headers=headers,
            json={
                "chassis": f"CHASSI-{uuid.uuid4().hex[:12]}", "axles": 3, "tare_weight": "8000.00",
                "load_capacity": "25000.00", "gross_vehicle_weight": "33000.00", "fuel_type": "DIESEL_S10",
            },
        )
        assert sheet_resp.status_code == 200, sheet_resp.text
        assert sheet_resp.json()["manufacturer"] == "Volvo"

        doc_resp = await client.post(
            f"/api/v1/veiculos/{vehicle_id}/documentos",
            headers=headers,
            json={"type": "CRLV", "number": "CRLV-001", "expires_at": "2099-01-01"},
        )
        assert doc_resp.status_code == 201, doc_resp.text
        assert doc_resp.json()["status"] == "VALIDO"

        docs_list = await client.get(f"/api/v1/veiculos/{vehicle_id}/documentos", headers=headers)
        assert docs_list.status_code == 200
        assert docs_list.json()["meta"]["pagination"]["total"] == 1

        deactivate = await client.delete(f"/api/v1/veiculos/{vehicle_id}", headers=headers)
        assert deactivate.status_code == 204

        after = await client.get(f"/api/v1/veiculos/{vehicle_id}", headers=headers)
        assert after.status_code == 404  # D343 — soft delete não aparece em consulta normal

        creation_logs = await _logs_for(tenant_id, "veiculos_tracionadores", "CRIACAO")
        assert uuid.UUID(vehicle_id) in creation_logs

    async def test_duplicate_plate_returns_409(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        plate = _plate("DUP")

        payload = {
            "plate": plate, "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Scania", "modelo": "R450",
            "ano_fabricacao": 2021, "categoria_id": str(category_id),
        }
        first = await client.post("/api/v1/veiculos", headers=headers, json=payload)
        assert first.status_code == 201

        payload2 = {**payload, "renavam": f"{uuid.uuid4().int % 10**11:011d}"}
        second = await client.post("/api/v1/veiculos", headers=headers, json=payload2)
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "FLEET_VEHICLE_PLATE_ALREADY_EXISTS"

    async def test_tenant_isolation_for_vehicles(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, _, category_b = await _full_access_actor(client, tenants)

        created = await client.post(
            "/api/v1/veiculos",
            headers=headers_b,
            json={
                "plate": _plate("ISO"), "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "DAF",
                "modelo": "XF", "ano_fabricacao": 2020, "categoria_id": str(category_b),
            },
        )
        assert created.status_code == 201
        vehicle_id = created.json()["id"]

        cross_tenant = await client.get(f"/api/v1/veiculos/{vehicle_id}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "FLEET_VEHICLE_NOT_FOUND"


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/veiculos",
        headers=headers,
        json={
            "plate": _plate("VEI"), "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Iveco",
            "modelo": "Way", "ano_fabricacao": 2023, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_implement(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/implementos",
        headers=headers,
        json={
            "plate": _plate("IMP"), "renavam": f"{uuid.uuid4().int % 10**11:011d}", "body_type": "CARRETA",
            "category_id": str(category_id), "load_capacity": "20000.00",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestImplementFlow:
    async def test_implement_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        implement_id = await _create_implement(client, headers, category_id)

        get_resp = await client.get(f"/api/v1/implementos/{implement_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["availability_status"] == "DISPONIVEL"

        patch_resp = await client.patch(
            f"/api/v1/implementos/{implement_id}", headers=headers, json={"availability_status": "EM_USO"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["availability_status"] == "EM_USO"

        deactivate = await client.delete(f"/api/v1/implementos/{implement_id}", headers=headers)
        assert deactivate.status_code == 204

    async def test_implement_in_active_composition_blocks_deactivation(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        implement_id = await _create_implement(client, headers, category_id)

        composition = await client.post(
            "/api/v1/vehicle-compositions",
            headers=headers,
            json={
                "tractor_unit_id": vehicle_id, "combination_type": "SIMPLES", "total_axles": 3,
                "implements": [{"implement_id": implement_id, "order": 1}],
            },
        )
        assert composition.status_code == 201, composition.text

        blocked = await client.delete(f"/api/v1/implementos/{implement_id}", headers=headers)
        assert blocked.status_code == 422
        assert blocked.json()["error"]["code"] == "FLEET_IMPLEMENT_IN_COMPOSITION"


class TestVehicleCompositionFlow:
    async def test_creating_a_new_composition_closes_the_previous_one(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        implement_1 = await _create_implement(client, headers, category_id)
        implement_2 = await _create_implement(client, headers, category_id)

        first = await client.post(
            "/api/v1/vehicle-compositions",
            headers=headers,
            json={
                "tractor_unit_id": vehicle_id, "combination_type": "SIMPLES", "total_axles": 3,
                "implements": [{"implement_id": implement_1, "order": 1}],
            },
        )
        assert first.status_code == 201, first.text
        first_id = first.json()["id"]
        assert first.json()["ends_at"] is None

        second = await client.post(
            "/api/v1/vehicle-compositions",
            headers=headers,
            json={
                "tractor_unit_id": vehicle_id, "combination_type": "BITREM", "total_axles": 7,
                "implements": [
                    {"implement_id": implement_1, "order": 1}, {"implement_id": implement_2, "order": 2}
                ],
            },
        )
        assert second.status_code == 201, second.text
        second_id = second.json()["id"]
        assert second.json()["ends_at"] is None

        first_after = await client.get(f"/api/v1/vehicle-compositions/{first_id}", headers=headers)
        assert first_after.status_code == 200
        assert first_after.json()["ends_at"] is not None

        vigentes = await client.get(
            "/api/v1/vehicle-compositions", headers=headers, params={"veiculo_tracionador_id": vehicle_id, "vigente": "true"}
        )
        assert vigentes.status_code == 200
        assert [c["id"] for c in vigentes.json()["data"]] == [second_id]

        validate = await client.post(f"/api/v1/vehicle-compositions/{second_id}/commands/validate", headers=headers)
        assert validate.status_code == 200
        assert validate.json()["status"] in {"VALIDA", "INVALIDA"}

    async def test_axle_mismatch_returns_422(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        response = await client.post(
            "/api/v1/vehicle-compositions",
            headers=headers,
            json={"tractor_unit_id": vehicle_id, "combination_type": "SIMPLES", "total_axles": 20, "implements": []},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "FLEET_COMPOSITION_AXLES_MISMATCH"

    async def test_never_two_current_compositions_for_the_same_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        """Auditoria dedicada pedida explicitamente pelo usuário — prova por comportamento
        observado (consulta direta ao banco a cada passo), não só confia no índice único."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        implements = [await _create_implement(client, headers, category_id) for _ in range(3)]

        session_factory = get_session_factory()

        for i, implement_id in enumerate(implements):
            response = await client.post(
                "/api/v1/vehicle-compositions",
                headers=headers,
                json={
                    "tractor_unit_id": vehicle_id, "combination_type": "SIMPLES", "total_axles": 3,
                    "implements": [{"implement_id": implement_id, "order": 1}],
                },
            )
            assert response.status_code == 201, response.text

            async with session_factory() as session:
                current_count = (
                    await session.execute(
                        select(VehicleCompositionModel.id).where(
                            VehicleCompositionModel.veiculo_tracionador_id == uuid.UUID(vehicle_id),
                            VehicleCompositionModel.data_fim_vigencia.is_(None),
                        )
                    )
                ).all()
            assert len(current_count) == 1, f"passo {i}: esperado exatamente 1 composição vigente, achou {len(current_count)}"


class TestOdometerReadingFlow:
    async def test_readings_reject_regression_and_paginate_by_cursor(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        first = await client.post(
            f"/api/v1/veiculos/{vehicle_id}/odometro/leituras", headers=headers, json={"value_km": "1000.00", "origin": "MANUAL"}
        )
        assert first.status_code == 201, first.text

        second = await client.post(
            f"/api/v1/veiculos/{vehicle_id}/odometro/leituras", headers=headers, json={"value_km": "1200.00", "origin": "CHECKLIST"}
        )
        assert second.status_code == 201

        regressed = await client.post(
            f"/api/v1/veiculos/{vehicle_id}/odometro/leituras", headers=headers, json={"value_km": "900.00", "origin": "MANUAL"}
        )
        assert regressed.status_code == 422
        assert regressed.json()["error"]["code"] == "FLEET_ODOMETER_READING_LOWER_THAN_LAST"

        first_page = await client.get(
            f"/api/v1/veiculos/{vehicle_id}/odometro/leituras", headers=headers, params={"limit": 1}
        )
        assert first_page.status_code == 200
        body = first_page.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["value_km"] == "1200.00"
        assert body["meta"]["pagination"]["has_more"] is True
        assert "page" not in body["meta"]["pagination"]
        assert "total" not in body["meta"]["pagination"]

        next_cursor = body["meta"]["pagination"]["next_cursor"]
        second_page = await client.get(
            f"/api/v1/veiculos/{vehicle_id}/odometro/leituras", headers=headers, params={"limit": 1, "cursor": next_cursor}
        )
        assert second_page.status_code == 200
        body2 = second_page.json()
        assert len(body2["data"]) == 1
        assert body2["data"][0]["value_km"] == "1000.00"
        assert body2["meta"]["pagination"]["has_more"] is False

        creation_logs = await _logs_for(tenant_id, "leituras_hodometro", "CRIACAO")
        assert len(creation_logs) == 2


class TestVehicleAvailabilityFlow:
    async def test_no_projection_until_first_signal_and_no_write_endpoint_exists(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        """Auditoria dedicada pedida explicitamente pelo usuário — prova que
        `disponibilidade_veiculo` não tem nenhum caminho de escrita HTTP."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        before = await client.get(f"/api/v1/veiculos/{vehicle_id}/disponibilidade", headers=headers)
        assert before.status_code == 404
        assert before.json()["error"]["code"] == "FLEET_VEHICLE_AVAILABILITY_NOT_FOUND"

        # Nenhuma rota de escrita existe para este recurso — confirmado tentando os três verbos.
        for verb in ("post", "patch", "delete"):
            response = await getattr(client, verb)(f"/api/v1/veiculos/{vehicle_id}/disponibilidade", headers=headers)
            assert response.status_code == 405, f"{verb.upper()} não deveria estar registrado"
        post_collection = await client.post("/api/v1/veiculos/disponibilidade", headers=headers)
        assert post_collection.status_code == 405

        # A única forma real de popular a projeção: o projetor de eventos, chamado diretamente
        # aqui simulando o que um consumidor real de `ViagemDespachada` faria (freight ainda não
        # existe no backend, AVAILABILITY_IMPLEMENTATION.md). `motorista_atual_id` tem FK real
        # para `motoristas` — usa um Motorista real (Lote 3), não um UUID solto.
        driver_resp = await client.post(
            "/api/v1/drivers",
            headers=headers,
            json={"nome": "Motorista de Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
        )
        assert driver_resp.status_code == 201, driver_resp.text
        driver_id = uuid.UUID(driver_resp.json()["id"])

        projector = VehicleAvailabilityProjector()
        token = set_current_tenant_id(tenant_id)
        try:
            await projector.apply_trip_dispatched(
                vehicle_id=uuid.UUID(vehicle_id), driver_id=driver_id, implement_id=None,
                at=datetime.now(timezone.utc),
            )
        finally:
            reset_current_tenant_id(token)

        after = await client.get(f"/api/v1/veiculos/{vehicle_id}/disponibilidade", headers=headers)
        assert after.status_code == 200
        assert after.json()["status"] == "EM_VIAGEM"

        list_resp = await client.get("/api/v1/veiculos/disponibilidade", headers=headers, params={"status": "EM_VIAGEM"})
        assert list_resp.status_code == 200
        assert any(a["vehicle_id"] == vehicle_id for a in list_resp.json()["data"])
