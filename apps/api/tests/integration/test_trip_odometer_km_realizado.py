from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import FiscalConfigurationModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.application.trip_odometer_recorder import TripOdometerRecorder
from modules.fleet.infrastructure.persistence.models.odometer_reading_model import OdometerReadingModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.documents.infrastructure.persistence.models.cte_model import CteModel, CteStatusHistoryModel
from modules.freight.infrastructure.persistence.models.delivery_model import DeliveryModel
from modules.freight.infrastructure.persistence.models.proof_of_delivery_model import ProofOfDeliveryModel
from modules.freight.infrastructure.persistence.models.trip_allocation_model import TripAllocationModel
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.freight.infrastructure.persistence.models.trip_status_history_model import TripStatusHistoryModel
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
"""V1 Operational Hardening, Parte 2 — KM real por Viagem. Prova a reconciliação formalizada em
`docs/domain/003-frota.md`/`docs/database/dictionary/002-operacao.md`: `Trip.km_rodado` passa a ser
`leitura_encerramento.valor_km - leitura_despacho.valor_km`, as duas leituras de fronteira gravadas
em `leituras_hodometro` (nunca uma segunda fonte da verdade) via `TripOdometerRecorder` (`fleet`).
Prova também os invariantes pedidos: hodômetro nunca decresce, km nunca negativo, km nunca estimado
quando faltar uma leitura, e idempotência do registro de fronteira contra reprocessamento."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.dispatch", "Despachar viagem", "freight"),
    ("freight.trip.finish", "Finalizar viagem", "freight"),
    ("freight.delivery.view", "Ver entregas", "freight"),
    ("freight.delivery.create", "Criar entregas", "freight"),
    ("freight.delivery.edit", "Editar entregas", "freight"),
    ("freight.pod.create", "Registrar canhoto", "freight"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]


async def _seed_permissions() -> None:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        for codigo, nome, modulo in PERMISSION_CATALOG:
            existing = (
                await session.execute(select(PermissionModel).where(PermissionModel.codigo == codigo))
            ).scalar_one_or_none()
            if existing is None:
                session.add(PermissionModel(id=uuid.uuid4(), codigo=codigo, nome=nome, modulo=modulo, criado_em=now))
        await session.commit()


async def _create_tenant() -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    tenant_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=tenant_id, codigo=f"T-{tenant_id.hex[:8]}", versao=1, razao_social="Transportadora KM LTDA",
                cnpj=f"{tenant_id.int % 10**14:014d}", status="ATIVO", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return tenant_id


async def _seed_vehicle_category(tenant_id: uuid.UUID) -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    category_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            VehicleCategoryModel(
                id=category_id, tenant_id=tenant_id, codigo=f"CAT-{category_id.hex[:8]}",
                nome=f"Categoria {category_id.hex[:6]}", status="ATIVA", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return category_id


async def _seed_fiscal_configuration(tenant_id: uuid.UUID) -> None:
    """D396 — despachar uma Viagem cria um CT-e automaticamente, o que exige uma
    `FiscalConfiguration` para o tenant. Seed direto via Repository, mesmo padrão de
    `test_financeiro_flow.py`."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            FiscalConfigurationModel(
                id=uuid.uuid4(), tenant_id=tenant_id, certificado_arquivo_id=uuid.uuid4(),
                certificado_validade=date(2030, 1, 1), ambiente="HOMOLOGACAO", regime_tributario="SIMPLES",
                serie_cte="1", proximo_numero_cte=1, serie_mdfe="1", proximo_numero_mdfe=1, status="ATIVA",
            )
        )
        await session.commit()


async def _create_role(tenant_id: uuid.UUID, permission_codes: list[str]) -> uuid.UUID:
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateRoleHandler().handle(
            CreateRoleCommand(
                actor=bootstrap_actor, nome=f"Papel-{uuid.uuid4().hex[:8]}", descricao=None,
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
                actor=bootstrap_actor, nome="Usuário de Teste", email=email, password=PASSWORD, driver_id=None,
                employee_id=None, role_ids=role_ids,
            )
        )
        return dto.id, email
    finally:
        reset_current_tenant_id(token)


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(delete(ProofOfDeliveryModel).where(ProofOfDeliveryModel.tenant_id == tenant_id))
        await session.execute(delete(DeliveryModel).where(DeliveryModel.tenant_id == tenant_id))
        await session.execute(delete(OdometerReadingModel).where(OdometerReadingModel.tenant_id == tenant_id))
        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(
            delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id)
        )
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleImpedimentModel).where(VehicleImpedimentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
        await session.execute(delete(ClientModel).where(ClientModel.tenant_id == tenant_id))
        await session.execute(usuarios_papeis.delete().where(usuarios_papeis.c.usuario_id.in_(
            select(UserModel.id).where(UserModel.tenant_id == tenant_id)
        )))
        await session.execute(papel_permissao.delete().where(papel_permissao.c.papel_id.in_(
            select(RoleModel.id).where(RoleModel.tenant_id == tenant_id)
        )))
        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


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


async def _setup(client: AsyncClient, tenants: list[uuid.UUID]) -> dict[str, Any]:
    await _seed_permissions()
    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    category_id = await _seed_vehicle_category(tenant_id)
    await _seed_fiscal_configuration(tenant_id)
    return {"tenant_id": tenant_id, "headers": headers, "category_id": category_id}


async def _create_client_(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/clients", headers=headers,
        json={"razao_social": f"Cliente {uuid.uuid4().hex[:6]}", "document": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_driver(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/drivers", headers=headers,
        json={"nome": f"Motorista {uuid.uuid4().hex[:6]}", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": f"KM{uuid.uuid4().hex[:5].upper()}", "renavam": f"{uuid.uuid4().int % 10**11:011d}",
            "fabricante": "Volvo", "modelo": "FH 540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_trip(client: AsyncClient, headers: dict[str, str], client_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": str(client_id)})
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _dispatch_trip_to_em_entrega(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, *,
    trip_id: uuid.UUID, driver_id: uuid.UUID, vehicle_id: uuid.UUID, departure_odometer_km: str | None,
) -> tuple[uuid.UUID, dict[str, Any]]:
    """Leva a Viagem até `EM_ENTREGA` (pré-condição de `commands/finish`) — mesmo template de
    `_advance_to_em_entrega` (`test_financeiro_flow.py`), com o corpo de despacho aceitando
    `departure_odometer_km` (V1 Operational Hardening, Parte 2)."""

    resources = await client.post(
        f"/api/v1/viagens/{trip_id}/resources", headers=headers,
        json={"driver_id": str(driver_id), "tractor_unit_id": str(vehicle_id)},
    )
    assert resources.status_code == 201, resources.text

    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=trip_id, now=now)
        await simulator.approve_checklist(trip_id=trip_id, now=now)
    finally:
        reset_current_tenant_id(token)

    dispatch_body = {"departure_odometer_km": departure_odometer_km} if departure_odometer_km is not None else {}
    dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers, json=dispatch_body)
    assert dispatch.status_code == 200, dispatch.text

    delivery_resp = await client.post(
        f"/api/v1/viagens/{trip_id}/entregas", headers=headers,
        json={"order": 1, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
    )
    assert delivery_resp.status_code == 201, delivery_resp.text
    delivery_id = uuid.UUID(delivery_resp.json()["id"])

    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.register_collection(trip_id=trip_id, now=now)
        await simulator.confirm_manifest(trip_id=trip_id, now=now)
    finally:
        reset_current_tenant_id(token)

    update = await client.patch(
        f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
    )
    assert update.status_code == 200, update.text

    canhoto = await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
    assert canhoto.status_code == 201, canhoto.text

    return delivery_id, dispatch.json()


@pytest.fixture
async def scenario(client: AsyncClient, tenants: list[uuid.UUID]) -> dict[str, Any]:
    ctx = await _setup(client, tenants)
    headers, tenant_id = ctx["headers"], ctx["tenant_id"]
    client_id = await _create_client_(client, headers)
    driver_id = await _create_driver(client, headers)
    vehicle_id = await _create_vehicle(client, headers, ctx["category_id"])
    trip_id = await _create_trip(client, headers, client_id)
    return {
        "headers": headers, "tenant_id": tenant_id, "client_id": client_id, "driver_id": driver_id,
        "vehicle_id": vehicle_id, "trip_id": trip_id,
    }


async def test_km_rodado_computed_from_departure_and_arrival_readings(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    trip_id, headers, tenant_id = scenario["trip_id"], scenario["headers"], scenario["tenant_id"]

    await _dispatch_trip_to_em_entrega(
        client, headers, tenant_id, trip_id=trip_id, driver_id=scenario["driver_id"],
        vehicle_id=scenario["vehicle_id"], departure_odometer_km="100000.00",
    )

    finish = await client.post(
        f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers, json={"arrival_odometer_km": "100250.50"}
    )
    assert finish.status_code == 200, finish.text
    assert finish.json()["status"]["operational"] == "FINALIZADA"

    trip = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
    assert trip.status_code == 200, trip.text
    assert Decimal(trip.json()["distance_traveled_km"]) == Decimal("250.50")

    # As duas leituras de fronteira existem em `leituras_hodometro` — nenhuma segunda fonte da
    # verdade: `km_rodado` é só a diferença entre elas, nunca um valor digitado à parte.
    session_factory = get_session_factory()
    async with session_factory() as session:
        readings = (
            await session.execute(
                select(OdometerReadingModel)
                .where(OdometerReadingModel.viagem_id == trip_id)
                .order_by(OdometerReadingModel.data_hora)
            )
        ).scalars().all()
    assert [r.origem for r in readings] == ["DESPACHO_VIAGEM", "ENCERRAMENTO_VIAGEM"]
    assert readings[0].valor_km == Decimal("100000.00")
    assert readings[1].valor_km == Decimal("100250.50")


async def test_km_rodado_stays_unavailable_without_odometer_readings(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """Regra fundamental do usuário: sem as duas leituras, `km_rodado` nunca é estimado — fica
    `None` ("Indisponível" no `/resultados`), nunca `0` ou um valor inventado."""

    trip_id, headers, tenant_id = scenario["trip_id"], scenario["headers"], scenario["tenant_id"]

    await _dispatch_trip_to_em_entrega(
        client, headers, tenant_id, trip_id=trip_id, driver_id=scenario["driver_id"],
        vehicle_id=scenario["vehicle_id"], departure_odometer_km=None,
    )
    finish = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers, json={})
    assert finish.status_code == 200, finish.text

    trip = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
    assert trip.json()["distance_traveled_km"] is None


async def test_arrival_lower_than_departure_is_rejected_never_negative_km(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """"Hodômetro nunca decresce" (D365) aplicado à leitura de encerramento — km_rodado nunca fica
    negativo porque a leitura inválida nunca chega a ser gravada."""

    trip_id, headers, tenant_id = scenario["trip_id"], scenario["headers"], scenario["tenant_id"]

    await _dispatch_trip_to_em_entrega(
        client, headers, tenant_id, trip_id=trip_id, driver_id=scenario["driver_id"],
        vehicle_id=scenario["vehicle_id"], departure_odometer_km="50000.00",
    )

    finish = await client.post(
        f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers, json={"arrival_odometer_km": "49000.00"}
    )
    assert finish.status_code == 422, finish.text
    assert finish.json()["error"]["code"] == "FLEET_ODOMETER_READING_LOWER_THAN_LAST"

    # A transição de status da Viagem já havia comitado antes do registro de hodômetro (mesmo
    # trade-off já aceito para CT-e/Disponibilidade neste módulo) — mas km_rodado nunca é gravado
    # com um valor inválido: fica indisponível, nunca negativo.
    trip = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
    assert trip.json()["status"]["operational"] == "FINALIZADA"
    assert trip.json()["distance_traveled_km"] is None


async def test_recording_the_same_boundary_reading_twice_is_idempotent(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """Corrige retry/idempotência (pedido explícito): reprocessar o mesmo registro de fronteira
    nunca cria uma segunda linha nem dispara "hodômetro decresce" contra si mesma."""

    trip_id, tenant_id = scenario["trip_id"], scenario["tenant_id"]
    token = set_current_tenant_id(tenant_id)
    try:
        recorder = TripOdometerRecorder()
        now = datetime.now(timezone.utc)
        first = await recorder.record_departure(
            vehicle_id=scenario["vehicle_id"], trip_id=trip_id, value_km=Decimal("77000.00"), now=now,
        )
        second = await recorder.record_departure(
            vehicle_id=scenario["vehicle_id"], trip_id=trip_id, value_km=Decimal("77000.00"), now=now,
        )
        assert second.id == first.id  # mesma leitura devolvida, nunca uma segunda criada

        session_factory = get_session_factory()
        async with session_factory() as session:
            count = (
                await session.execute(
                    select(OdometerReadingModel).where(
                        OdometerReadingModel.viagem_id == trip_id,
                        OdometerReadingModel.origem == "DESPACHO_VIAGEM",
                    )
                )
            ).scalars().all()
        assert len(count) == 1
    finally:
        reset_current_tenant_id(token)
