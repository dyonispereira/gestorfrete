from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
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
from modules.tracking.application.tracking_ingestion import TrackingIngestion
from modules.tracking.domain.entities.location_origin import LocationOrigin
from modules.tracking.domain.value_objects.sensor_type import SensorType
from modules.tracking.infrastructure.persistence.models.geofence_model import GeofenceModel
from modules.tracking.infrastructure.persistence.models.heartbeat_model import HeartbeatModel
from modules.tracking.infrastructure.persistence.models.speed_limit_config_model import SpeedLimitConfigModel
from modules.tracking.infrastructure.persistence.models.telemetry_reading_model import TelemetryReadingModel
from modules.tracking.infrastructure.persistence.models.tracking_equipment_model import TrackingEquipmentModel
from modules.tracking.infrastructure.persistence.models.tracking_event_model import TrackingEventModel
from modules.tracking.infrastructure.persistence.models.tracking_provider_model import TrackingProviderModel
from modules.tracking.infrastructure.persistence.models.vehicle_position_model import VehiclePositionModel
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_location_origin_repository import (
    SqlAlchemyLocationOriginRepository,
)
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 8 — Rastreamento (D402-D406). D352 aplicado aos agregados com CRUD real
(Provedor/Equipamento/Geofence/Configuração de Limite de Velocidade), mais as sete auditorias
explicitamente pedidas pelo usuário: (1) imutabilidade de Time Series; (2) três timestamps
distintos (+ exceção D191 do Heartbeat); (3) geofence real via PostGIS; (4) telemetria EAV; (5)
evento derivado nunca muta Viagem; (6) equipamento único PRINCIPAL, testado direto contra o banco;
(7) paginação por cursor."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("tracking.provider.view", "Ver provedor de rastreamento", "tracking"),
    ("tracking.provider.create", "Criar provedor de rastreamento", "tracking"),
    ("tracking.provider.edit", "Editar provedor de rastreamento", "tracking"),
    ("tracking.equipment.view", "Ver equipamento de rastreamento", "tracking"),
    ("tracking.equipment.create", "Criar equipamento de rastreamento", "tracking"),
    ("tracking.equipment.edit", "Editar equipamento de rastreamento", "tracking"),
    ("tracking.position.view", "Ver posição de veículo", "tracking"),
    ("tracking.telemetry.view", "Ver leitura de telemetria", "tracking"),
    ("tracking.heartbeat.view", "Ver heartbeat", "tracking"),
    ("tracking.geofence.view", "Ver geofence", "tracking"),
    ("tracking.geofence.create", "Criar geofence", "tracking"),
    ("tracking.geofence.edit", "Editar geofence", "tracking"),
    ("tracking.geofence.delete", "Excluir geofence", "tracking"),
    ("tracking.stop.view", "Ver paradas", "tracking"),
    ("tracking.route_deviation.view", "Ver desvios de rota", "tracking"),
    ("tracking.speed_event.view", "Ver eventos de velocidade", "tracking"),
    ("tracking.speed_limit_config.view", "Ver configuração de limite de velocidade", "tracking"),
    ("tracking.speed_limit_config.create", "Criar configuração de limite de velocidade", "tracking"),
    ("tracking.speed_limit_config.edit", "Editar configuração de limite de velocidade", "tracking"),
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


async def _seed_location_origins() -> None:
    # D406 — mesmo precedente de `permissoes`: seed idempotente via helper de teste, nunca migration.
    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = SqlAlchemyLocationOriginRepository(session)
        for nome in ("GPS", "GSM", "Satélite", "Wi-Fi", "BLE", "Manual", "API Externa"):
            await repo.add(LocationOrigin(id=uuid.uuid4(), nome=nome, precisao_tipica_metros=None))
        await session.commit()


async def _gps_origin_id() -> uuid.UUID:
    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = SqlAlchemyLocationOriginRepository(session)
        origin = await repo.get_by_nome("GPS")
        assert origin is not None
        return origin.id


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


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _full_access_actor(client: AsyncClient, tenants: list[uuid.UUID]) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    """Retorna (headers, tenant_id, category_id)."""

    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    category_id = await _seed_vehicle_category(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    return headers, tenant_id, category_id


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))).scalars().all()
        role_ids = (await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))).scalars().all()

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))

        # Tracking — filhos antes dos pais.
        await session.execute(delete(TrackingEventModel).where(TrackingEventModel.tenant_id == tenant_id))
        await session.execute(delete(HeartbeatModel).where(HeartbeatModel.tenant_id == tenant_id))
        await session.execute(delete(TelemetryReadingModel).where(TelemetryReadingModel.tenant_id == tenant_id))
        await session.execute(delete(VehiclePositionModel).where(VehiclePositionModel.tenant_id == tenant_id))
        await session.execute(delete(SpeedLimitConfigModel).where(SpeedLimitConfigModel.tenant_id == tenant_id))
        await session.execute(delete(GeofenceModel).where(GeofenceModel.tenant_id == tenant_id))
        await session.execute(delete(TrackingEquipmentModel).where(TrackingEquipmentModel.tenant_id == tenant_id))
        await session.execute(delete(TrackingProviderModel).where(TrackingProviderModel.tenant_id == tenant_id))

        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
        await session.execute(delete(ClientModel).where(ClientModel.tenant_id == tenant_id))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


@pytest.fixture
async def permission_ids() -> dict[str, uuid.UUID]:
    return await _seed_permissions()


@pytest.fixture
async def location_origins() -> None:
    await _seed_location_origins()


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


# --------------------------------------------------------------------------------------
# Helpers de domínio
# --------------------------------------------------------------------------------------


async def _create_client_entity(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/clients", headers=headers,
        json={"razao_social": "Cliente de Teste LTDA", "document": f"{uuid.uuid4().int % 10**11:011d}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_driver(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/drivers", headers=headers,
        json={"nome": "Motorista de Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": f"VG{uuid.uuid4().hex[:5].upper()}", "renavam": f"{uuid.uuid4().int % 10**11:011d}",
            "fabricante": "Volvo", "modelo": "FH540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_trip_with_vehicle(
    client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID
) -> tuple[str, str]:
    """Cria Viagem + aloca veículo, sem despachar — suficiente para provar a Auditoria #5 (Evento de
    Rastreamento nunca muda `status.operational`). Retorna (trip_id, vehicle_id)."""

    client_id = await _create_client_entity(client, headers)
    driver_id = await _create_driver(client, headers)
    vehicle_id = await _create_vehicle(client, headers, category_id)

    create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert create.status_code == 201, create.text
    trip_id = create.json()["id"]

    allocation = await client.post(
        f"/api/v1/viagens/{trip_id}/resources", headers=headers,
        json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
    )
    assert allocation.status_code == 201, allocation.text
    return trip_id, vehicle_id


async def _create_provider(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post("/api/v1/tracking/providers", headers=headers, json={"name": "Sascar"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_principal_equipment(
    client: AsyncClient, headers: dict[str, str], provider_id: str, vehicle_id: str
) -> str:
    resp = await client.post(
        "/api/v1/tracking/equipment", headers=headers,
        json={
            "provider_id": provider_id, "serial_identifier": f"IMEI-{uuid.uuid4().hex[:12]}",
            "equipment_type": "PRINCIPAL", "vehicle_id": vehicle_id,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestTrackingProviderAndEquipmentFlow:
    """D352 — Provedor/Equipamento, CRUD real via HTTP."""

    async def test_provider_and_equipment_crud(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)

        duplicate = await client.post("/api/v1/tracking/providers", headers=headers, json={"name": "Sascar"})
        assert duplicate.status_code == 409, duplicate.text
        assert duplicate.json()["error"]["code"] == "TRACKING_PROVIDER_NAME_ALREADY_EXISTS"

        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        get_equipment = await client.get(f"/api/v1/tracking/equipment/{equipment_id}", headers=headers)
        assert get_equipment.status_code == 200
        assert get_equipment.json()["equipment_type"] == "PRINCIPAL"
        assert get_equipment.json()["vehicle_id"] == vehicle_id

        edit_provider = await client.patch(
            f"/api/v1/tracking/providers/{provider_id}", headers=headers, json={"status": "INATIVO"}
        )
        assert edit_provider.status_code == 200
        assert edit_provider.json()["status"] == "INATIVO"


class TestSinglePrincipalEquipmentAudit:
    """Auditoria #6 do usuário (D128) — no máximo um equipamento PRINCIPAL vigente por veículo,
    testado tanto pela API quanto diretamente contra o banco."""

    async def test_second_principal_via_api_is_rejected(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        second = await client.post(
            "/api/v1/tracking/equipment", headers=headers,
            json={
                "provider_id": provider_id, "serial_identifier": f"IMEI-{uuid.uuid4().hex[:12]}",
                "equipment_type": "PRINCIPAL", "vehicle_id": vehicle_id,
            },
        )
        assert second.status_code == 409, second.text
        assert second.json()["error"]["code"] == "TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS"

        # Papéis distintos (BACKUP) coexistem livremente com o PRINCIPAL vigente (D128).
        backup = await client.post(
            "/api/v1/tracking/equipment", headers=headers,
            json={
                "provider_id": provider_id, "serial_identifier": f"IMEI-{uuid.uuid4().hex[:12]}",
                "equipment_type": "BACKUP", "vehicle_id": vehicle_id,
            },
        )
        assert backup.status_code == 201, backup.text

    async def test_constraint_is_physical_not_only_application_level(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        session_factory = get_session_factory()
        async with session_factory() as session:
            with pytest.raises(Exception) as exc_info:
                await session.execute(
                    text(
                        "INSERT INTO equipamentos_rastreamento "
                        "(id, tenant_id, provedor_rastreamento_id, identificador_serial, tipo_equipamento, "
                        "veiculo_tracionador_id, status) "
                        "VALUES (gen_random_uuid(), :tenant_id, :provider_id, :serial, 'PRINCIPAL', :vehicle_id, 'ATIVO')"
                    ),
                    {
                        "tenant_id": str(tenant_id), "provider_id": provider_id,
                        "serial": f"IMEI-{uuid.uuid4().hex[:12]}", "vehicle_id": vehicle_id,
                    },
                )
                await session.flush()
            assert "uq_equipamentos_rastreamento_principal_vigente" in str(exc_info.value)
            await session.rollback()


class TestTimeSeriesImmutabilityAudit:
    """Auditoria #1 do usuário — Posição/Telemetria/Heartbeat sem `PATCH`/`DELETE`; uma leitura
    persistida nunca é sobrescrita por uma leitura nova."""

    async def test_no_write_endpoints_exist(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        patch_position = await client.patch(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions/{uuid.uuid4()}", headers=headers, json={}
        )
        assert patch_position.status_code == 404
        delete_position = await client.delete(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions/{uuid.uuid4()}", headers=headers
        )
        assert delete_position.status_code == 404
        # Mesmo path do `GET` registrado, método diferente — Starlette responde 405 (rota existe,
        # verbo não), não 404 (que seria "nenhuma rota casa com este path").
        post_position = await client.post(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers, json={}
        )
        assert post_position.status_code == 405

    async def test_new_reading_never_overwrites_a_previous_one(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        token = set_current_tenant_id(tenant_id)
        try:
            base = datetime.now(timezone.utc) - timedelta(hours=1)
            first = await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.5,
                longitude=-46.6, origin_id=origin_id, captured_at=base,
            )
            second = await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.6,
                longitude=-46.7, origin_id=origin_id, captured_at=base + timedelta(minutes=5),
            )
        finally:
            reset_current_tenant_id(token)

        listed = await client.get(f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers)
        assert listed.status_code == 200
        ids = {item["id"] for item in listed.json()["data"]}
        assert str(first.id) in ids
        assert str(second.id) in ids
        first_entry = next(item for item in listed.json()["data"] if item["id"] == str(first.id))
        assert first_entry["location"]["latitude"] == -23.5


class TestThreeTimestampsAudit:
    """Auditoria #2 do usuário — `capturado_em`/`recebido_em`/`processado_em` distintos para
    Posição/Telemetria; exceção D191 do Heartbeat (`capturado_em` pode ser `None`)."""

    async def test_position_has_three_distinct_timestamps(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        captured = datetime.now(timezone.utc) - timedelta(minutes=10)
        received = captured + timedelta(seconds=30)
        processed = received + timedelta(seconds=2)

        token = set_current_tenant_id(tenant_id)
        try:
            await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.5,
                longitude=-46.6, origin_id=origin_id, captured_at=captured, received_at=received,
                processed_at=processed,
            )
        finally:
            reset_current_tenant_id(token)

        listed = await client.get(f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers)
        entry = listed.json()["data"][0]
        assert entry["captured_at"] != entry["received_at"] != entry["processed_at"]
        assert datetime.fromisoformat(entry["captured_at"]) < datetime.fromisoformat(entry["received_at"])
        assert datetime.fromisoformat(entry["received_at"]) < datetime.fromisoformat(entry["processed_at"])

    async def test_heartbeat_allows_absent_capture_time(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        token = set_current_tenant_id(tenant_id)
        try:
            heartbeat = await TrackingIngestion().ingest_heartbeat(
                equipment_id=uuid.UUID(equipment_id), captured_at=None, received_at=datetime.now(timezone.utc),
            )
        finally:
            reset_current_tenant_id(token)
        assert heartbeat is not None

        listed = await client.get(f"/api/v1/tracking/equipment/{equipment_id}/heartbeats", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["data"][0]["captured_at"] is None
        assert listed.json()["data"][0]["received_at"] is not None


class TestGeofenceAudit:
    """Auditoria #3 do usuário — primeiro teste realmente geoespacial do backend: ponto dentro/fora
    de uma Cerca via PostGIS real, índice espacial usável."""

    async def test_circle_geofence_entry_and_exit(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        geofence = await client.post(
            "/api/v1/tracking/geofences", headers=headers,
            json={
                "name": "Pátio Central", "geometry_type": "CIRCULO",
                "center": {"latitude": -23.5505, "longitude": -46.6333}, "radius_meters": 200,
            },
        )
        assert geofence.status_code == 201, geofence.text
        geofence_id = geofence.json()["id"]

        base = datetime.now(timezone.utc) - timedelta(hours=1)
        token = set_current_tenant_id(tenant_id)
        try:
            # Dentro do raio (mesmo ponto do centro).
            await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.5505,
                longitude=-46.6333, origin_id=origin_id, captured_at=base,
            )
            # Fora do raio — a ~5km de distância.
            await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.60,
                longitude=-46.68, origin_id=origin_id, captured_at=base + timedelta(minutes=5),
            )
        finally:
            reset_current_tenant_id(token)

        events = await client.get(
            "/api/v1/tracking/events", headers=headers, params={"vehicle_id": vehicle_id}
        )
        assert events.status_code == 200, events.text
        types = [e["type"] for e in events.json()["data"]]
        assert "ENTROU_GEOFENCE" in types
        assert "SAIU_GEOFENCE" in types
        entered = next(e for e in events.json()["data"] if e["type"] == "ENTROU_GEOFENCE")
        assert entered["geofence_id"] == geofence_id

    async def test_polygon_geofence_containment(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        polygon = [
            {"latitude": -23.55, "longitude": -46.64}, {"latitude": -23.55, "longitude": -46.62},
            {"latitude": -23.56, "longitude": -46.62}, {"latitude": -23.56, "longitude": -46.64},
        ]
        geofence = await client.post(
            "/api/v1/tracking/geofences", headers=headers,
            json={"name": "Zona Restrita", "geometry_type": "POLIGONO", "polygon": polygon},
        )
        assert geofence.status_code == 201, geofence.text

        base = datetime.now(timezone.utc) - timedelta(hours=1)
        token = set_current_tenant_id(tenant_id)
        try:
            # Dentro do polígono.
            await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.555,
                longitude=-46.63, origin_id=origin_id, captured_at=base,
            )
        finally:
            reset_current_tenant_id(token)

        events = await client.get(
            "/api/v1/tracking/events", headers=headers, params={"vehicle_id": vehicle_id, "type": "ENTROU_GEOFENCE"}
        )
        assert events.status_code == 200
        assert len(events.json()["data"]) == 1

    async def test_gist_spatial_index_exists_and_is_usable(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            index_exists = (
                await session.execute(
                    text(
                        "SELECT indexdef FROM pg_indexes WHERE tablename = 'posicoes_veiculo' "
                        "AND indexname = 'idx_posicoes_veiculo_localizacao'"
                    )
                )
            ).scalar_one_or_none()
            assert index_exists is not None
            assert "gist" in index_exists.lower()

            # Índice de fato utilizável pelo planner: com `enable_seqscan` desligado, o plano
            # precisa recorrer ao GiST para resolver a consulta espacial sem erro.
            await session.execute(text("SET LOCAL enable_seqscan = off"))
            plan_rows = (
                await session.execute(
                    text(
                        "EXPLAIN SELECT id FROM posicoes_veiculo WHERE ST_DWithin("
                        "localizacao, 'SRID=4326;POINT(-46.6333 -23.5505)'::geography, 500)"
                    )
                )
            ).all()
            plan_text = "\n".join(row[0] for row in plan_rows)
            # A partição física herda o índice com um nome derivado
            # (`posicoes_veiculo_default_localizacao_idx`), não o nome literal declarado na tabela
            # mãe — checa o sufixo estável em vez do nome exato.
            assert "Index Scan" in plan_text
            assert "localizacao_idx" in plan_text


class TestTelemetryEavAudit:
    """Auditoria #4 do usuário — dois sensores diferentes no mesmo instante sem coluna dedicada;
    `tipo_sensor` respeita um Enum controlado, nunca texto livre."""

    async def test_two_sensor_types_same_instant_persist_as_distinct_rows(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        same_instant = datetime.now(timezone.utc) - timedelta(minutes=1)
        token = set_current_tenant_id(tenant_id)
        try:
            await TrackingIngestion().ingest_telemetry(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), sensor_type=SensorType.RPM,
                value=1800, unit="RPM", captured_at=same_instant,
            )
            await TrackingIngestion().ingest_telemetry(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id),
                sensor_type=SensorType.TEMPERATURA, value=87.5, unit="°C", captured_at=same_instant,
            )
        finally:
            reset_current_tenant_id(token)

        listed = await client.get(f"/api/v1/vehicles/{vehicle_id}/tracking/telemetry", headers=headers)
        assert listed.status_code == 200
        sensor_types = {item["sensor_type"] for item in listed.json()["data"]}
        assert sensor_types == {"RPM", "TEMPERATURA"}
        assert len(listed.json()["data"]) == 2

    async def test_sensor_type_is_a_controlled_enum_never_free_text(self) -> None:
        with pytest.raises(ValueError):
            SensorType("SENSOR_INVENTADO_LIVRE")


class TestTrackingEventNeverMutatesTripAudit:
    """Auditoria #5 do usuário (D116/D285) — provavelmente a mais importante do lote: um Evento de
    Rastreamento derivado nunca muda `Trip.status_operacional`, mesmo quando o veículo envolvido
    está alocado à viagem."""

    async def test_geofence_event_never_changes_trip_operational_status(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id, vehicle_id = await _create_trip_with_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        before = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert before.status_code == 200
        status_before = before.json()["status"]["operational"]

        geofence = await client.post(
            "/api/v1/tracking/geofences", headers=headers,
            json={
                "name": "Cliente ABC", "geometry_type": "CIRCULO",
                "center": {"latitude": -23.5505, "longitude": -46.6333}, "radius_meters": 300,
            },
        )
        assert geofence.status_code == 201, geofence.text

        token = set_current_tenant_id(tenant_id)
        try:
            await TrackingIngestion().ingest_position(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.5505,
                longitude=-46.6333, origin_id=origin_id, captured_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        finally:
            reset_current_tenant_id(token)

        events = await client.get(
            "/api/v1/tracking/events", headers=headers,
            params={"vehicle_id": vehicle_id, "type": "ENTROU_GEOFENCE"},
        )
        assert len(events.json()["data"]) == 1  # o evento de fato foi criado...

        after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert after.status_code == 200
        # ...mas o status operacional da Viagem permanece byte-a-byte idêntico (D116/D285).
        assert after.json()["status"]["operational"] == status_before


class TestCursorPaginationAudit:
    """Auditoria #7 do usuário — primeiro uso realmente relevante do padrão de cursor: inserir
    várias leituras, buscar página 1, capturar cursor, buscar página 2, garantir zero
    duplicação/perda."""

    async def test_positions_paginate_without_duplication_or_loss(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID],
        location_origins: None,
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)
        origin_id = await _gps_origin_id()

        base = datetime.now(timezone.utc) - timedelta(hours=1)
        inserted_ids: set[str] = set()
        token = set_current_tenant_id(tenant_id)
        try:
            for i in range(5):
                position = await TrackingIngestion().ingest_position(
                    vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), latitude=-23.5 - i * 0.01,
                    longitude=-46.6, origin_id=origin_id, captured_at=base + timedelta(minutes=i),
                )
                inserted_ids.add(str(position.id))
        finally:
            reset_current_tenant_id(token)

        page1 = await client.get(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers, params={"limit": 2}
        )
        assert page1.status_code == 200
        page1_ids = {item["id"] for item in page1.json()["data"]}
        assert len(page1_ids) == 2
        assert page1.json()["meta"]["pagination"]["has_more"] is True
        cursor = page1.json()["meta"]["pagination"]["next_cursor"]
        assert cursor is not None

        page2 = await client.get(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers,
            params={"limit": 2, "cursor": cursor},
        )
        page2_ids = {item["id"] for item in page2.json()["data"]}
        assert len(page2_ids) == 2
        assert page1_ids.isdisjoint(page2_ids)  # zero duplicação
        cursor2 = page2.json()["meta"]["pagination"]["next_cursor"]

        page3 = await client.get(
            f"/api/v1/vehicles/{vehicle_id}/tracking/positions", headers=headers,
            params={"limit": 2, "cursor": cursor2},
        )
        page3_ids = {item["id"] for item in page3.json()["data"]}
        assert len(page3_ids) == 1
        assert page3.json()["meta"]["pagination"]["has_more"] is False

        all_ids = page1_ids | page2_ids | page3_ids
        assert all_ids == inserted_ids  # zero perda


class TestGeofenceCrudFlow:
    """D352 — Cerca Eletrônica/Configuração de Limite de Velocidade, CRUD real via HTTP."""

    async def test_geofence_and_speed_limit_config_crud(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/tracking/geofences", headers=headers,
            json={
                "name": "Filial Sul", "geometry_type": "CIRCULO",
                "center": {"latitude": -23.5, "longitude": -46.6}, "radius_meters": 100,
            },
        )
        assert create.status_code == 201, create.text
        geofence_id = create.json()["id"]

        update = await client.patch(
            f"/api/v1/tracking/geofences/{geofence_id}", headers=headers, json={"status": "INATIVA"}
        )
        assert update.status_code == 200
        assert update.json()["status"] == "INATIVA"

        delete = await client.delete(f"/api/v1/tracking/geofences/{geofence_id}", headers=headers)
        assert delete.status_code == 204

        after_delete = await client.get(f"/api/v1/tracking/geofences/{geofence_id}", headers=headers)
        assert after_delete.status_code == 200
        assert after_delete.json()["status"] == "INATIVA"  # soft delete (D219), nunca some (D001)

        speed_config = await client.post(
            "/api/v1/tracking/speed-limit-configs", headers=headers,
            json={"vehicle_category_id": str(category_id), "limit_kmh": "90"},
        )
        assert speed_config.status_code == 201, speed_config.text
        assert speed_config.json()["limit_kmh"] == "90.0"


class TestSpeedViolationEventFlow:
    async def test_telemetry_above_limit_creates_speed_event(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        provider_id = await _create_provider(client, headers)
        equipment_id = await _create_principal_equipment(client, headers, provider_id, vehicle_id)

        speed_config = await client.post(
            "/api/v1/tracking/speed-limit-configs", headers=headers,
            json={"vehicle_category_id": str(category_id), "limit_kmh": "80"},
        )
        assert speed_config.status_code == 201, speed_config.text

        token = set_current_tenant_id(tenant_id)
        try:
            await TrackingIngestion().ingest_telemetry(
                vehicle_id=uuid.UUID(vehicle_id), equipment_id=uuid.UUID(equipment_id), sensor_type=SensorType.VELOCIDADE,
                value=110, unit="km/h", vehicle_category_id=category_id,
                captured_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        finally:
            reset_current_tenant_id(token)

        events = await client.get(
            "/api/v1/tracking/events", headers=headers,
            params={"vehicle_id": vehicle_id, "type": "EXCESSO_DE_VELOCIDADE"},
        )
        assert events.status_code == 200
        assert len(events.json()["data"]) == 1
        assert events.json()["data"][0]["detected_value"] == "110.0"


class TestTenantIsolation:
    async def test_cross_tenant_provider_access_returns_404(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, _, _ = await _full_access_actor(client, tenants)

        provider_id = await _create_provider(client, headers_b)

        cross_tenant = await client.get(f"/api/v1/tracking/providers/{provider_id}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "TRACKING_PROVIDER_NOT_FOUND"
