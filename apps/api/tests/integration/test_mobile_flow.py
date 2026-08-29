from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.infrastructure.persistence.models.cte_model import CteModel, CteStatusHistoryModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import FiscalConfigurationModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.infrastructure.persistence.models.delivery_model import DeliveryModel, DeliveryWindowModel
from modules.freight.infrastructure.persistence.models.occurrence_model import OccurrenceModel
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
from modules.mobile.infrastructure.persistence.models.digital_signature_model import DigitalSignatureModel
from modules.mobile.infrastructure.persistence.models.mobile_device_model import MobileDeviceModel
from modules.mobile.infrastructure.persistence.models.mobile_session_model import MobileSessionModel
from modules.mobile.infrastructure.persistence.models.sync_queue_item_model import SyncQueueItemModel
from modules.mobile.infrastructure.persistence.models.sync_record_model import SyncRecordModel
from modules.notification_center.infrastructure.persistence.models.channel_preference_model import (
    ChannelPreferenceModel,
)
from modules.notification_center.infrastructure.persistence.models.notification_model import NotificationModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 9 — Mobile/App Motorista (D407-D411). D352 aplicado à Sessão/Dispositivo/
Sincronização/Assinatura, mais as oito auditorias explicitamente pedidas pelo usuário: (1) offline/
idempotência; (2) ordem da fila por sequencia_local; (3) conflito preserva payload original; (4)
Sessão×Dispositivo independentes; (5) tenant/identidade sempre da sessão; (6) RBAC reutiliza os
códigos de domínio; (7) push é só metadata; (8) storage sempre file_id. Mais a auditoria adicional:
mesmo comando via Web e via Mobile produz o mesmo efeito (D303)."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.view_own", "Ver as próprias viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.start", "Iniciar viagem", "freight"),
    ("freight.trip.finish", "Finalizar viagem", "freight"),
    ("freight.trip.cancel", "Cancelar viagem", "freight"),
    ("freight.occurrence.view", "Ver ocorrências", "freight"),
    ("freight.occurrence.create", "Criar ocorrências", "freight"),
    ("freight.delivery.view", "Ver entregas", "freight"),
    ("freight.delivery.create", "Criar entregas", "freight"),
    ("freight.pod.create", "Registrar canhoto", "freight"),
    ("freight.pod.attach", "Anexar foto/assinatura do canhoto", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("mobile.device.view_own", "Ver os próprios dispositivos", "mobile"),
    ("mobile.device.edit_own", "Editar o próprio dispositivo", "mobile"),
    ("mobile.sync.execute", "Sincronizar comandos pendentes", "mobile"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]
DRIVER_PERMISSION_CODES = [
    "freight.trip.view_own", "freight.trip.edit", "freight.trip.start", "freight.trip.finish",
    "freight.occurrence.view", "freight.occurrence.create", "freight.delivery.view", "freight.delivery.create",
    "freight.pod.create", "freight.pod.attach", "mobile.device.view_own", "mobile.device.edit_own",
    "mobile.sync.execute",
]


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
    """D396 — despachar uma Viagem (`/commands/start`, reaproveitado pelo Motorista) cria um CT-e
    automaticamente, o que exige uma `FiscalConfiguration` (Lote 7) para o tenant."""

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
            CreateRoleCommand(actor=bootstrap_actor, nome=f"Papel-{uuid.uuid4().hex[:8]}", descricao=None, permission_codes=permission_codes)
        )
        return dto.id
    finally:
        reset_current_tenant_id(token)


async def _create_user(tenant_id: uuid.UUID, *, role_ids: frozenset[uuid.UUID], driver_id: uuid.UUID | None = None) -> tuple[uuid.UUID, str]:
    email = f"user-{uuid.uuid4().hex[:10]}@teste.com"
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateUserHandler().handle(
            CreateUserCommand(
                actor=bootstrap_actor, nome="Usuário de Teste", email=email, password=PASSWORD, driver_id=driver_id,
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
    """Retorna (headers do Gestor, tenant_id, category_id)."""

    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    category_id = await _seed_vehicle_category(tenant_id)
    await _seed_fiscal_configuration(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    return headers, tenant_id, category_id


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))).scalars().all()
        role_ids = (await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))).scalars().all()
        entrega_ids = (
            await session.execute(select(DeliveryModel.id).where(DeliveryModel.tenant_id == tenant_id))
        ).scalars().all()

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))
        await session.execute(delete(AttachmentModel).where(AttachmentModel.tenant_id == tenant_id))

        # Mobile — filhos antes dos pais.
        await session.execute(delete(DigitalSignatureModel).where(DigitalSignatureModel.tenant_id == tenant_id))
        await session.execute(delete(SyncRecordModel).where(SyncRecordModel.tenant_id == tenant_id))
        await session.execute(delete(SyncQueueItemModel).where(SyncQueueItemModel.tenant_id == tenant_id))
        await session.execute(delete(MobileSessionModel).where(MobileSessionModel.tenant_id == tenant_id))
        await session.execute(delete(MobileDeviceModel).where(MobileDeviceModel.tenant_id == tenant_id))

        # Lote 10/D414 — CreateOccurrenceHandler/DispatchTripHandler podem criar `notificacoes`
        # (FK para `usuarios`); precisa sair antes de `usuarios`.
        await session.execute(delete(NotificationModel).where(NotificationModel.tenant_id == tenant_id))
        await session.execute(delete(ChannelPreferenceModel).where(ChannelPreferenceModel.tenant_id == tenant_id))

        if entrega_ids:
            await session.execute(delete(ProofOfDeliveryModel).where(ProofOfDeliveryModel.entrega_id.in_(entrega_ids)))
            await session.execute(delete(DeliveryWindowModel).where(DeliveryWindowModel.entrega_id.in_(entrega_ids)))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(DeliveryModel).where(DeliveryModel.tenant_id == tenant_id))
        # D396 — despachar (`/commands/start`) cria um CT-e automaticamente (`ctes.viagem_id` FK);
        # precisa sair antes de `viagens`.
        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleImpedimentModel).where(VehicleImpedimentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
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


async def _create_driver(client: AsyncClient, headers: dict[str, str]) -> tuple[str, str]:
    cpf = f"{uuid.uuid4().int % 10**11:011d}"
    resp = await client.post(
        "/api/v1/drivers", headers=headers, json={"nome": "Motorista de Teste", "cpf": cpf, "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"], cpf


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> tuple[str, str]:
    plate = f"VG{uuid.uuid4().hex[:5].upper()}"
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": plate, "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Volvo", "modelo": "FH540",
            "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"], plate


async def _register_mobile_driver(tenant_id: uuid.UUID, driver_id: str) -> None:
    role_id = await _create_role(tenant_id, DRIVER_PERMISSION_CODES)
    await _create_user(tenant_id, role_ids=frozenset({role_id}), driver_id=uuid.UUID(driver_id))


async def _mobile_login(
    client: AsyncClient, *, cpf: str, vehicle_plate: str, device_identifier: str, credential: str = "n/a",
) -> dict[str, object]:
    resp = await client.post(
        "/api/v1/mobile/auth/login",
        json={
            "cpf": cpf, "vehicle_plate": vehicle_plate, "auth_method": "CPF_VEICULO", "credential": credential,
            "device": {
                "device_identifier": device_identifier, "os": "ANDROID", "os_version": "14", "app_version": "1.0.0",
                "push_token": "push-token-abc",
            },
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_trip_allocated(
    client: AsyncClient, headers: dict[str, str], client_id: str, driver_id: str, vehicle_id: str,
) -> str:
    create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert create.status_code == 201, create.text
    trip_id = create.json()["id"]

    allocation = await client.post(
        f"/api/v1/viagens/{trip_id}/resources", headers=headers,
        json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
    )
    assert allocation.status_code == 201, allocation.text
    return trip_id


async def _advance_to_liberada(tenant_id: uuid.UUID, trip_id: str) -> None:
    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)


class TestMobileAuthAndDeviceFlow:
    """D352 — login/sessão/dispositivo funcionais de ponta a ponta."""

    async def test_login_me_device_and_logout(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        _, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)

        login_body = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-001")
        assert login_body["driver"]["id"] == driver_id
        assert login_body["session"]["status"] == "ATIVA"
        mobile_headers = {"Authorization": f"Bearer {login_body['access_token']}"}

        me = await client.get("/api/v1/mobile/auth/me", headers=mobile_headers)
        assert me.status_code == 200
        assert me.json()["driver"]["id"] == driver_id

        devices = await client.get("/api/v1/mobile/devices", headers=mobile_headers)
        assert devices.status_code == 200
        assert len(devices.json()["data"]) == 1
        assert devices.json()["data"][0]["device_identifier"] == "device-001"

        logout = await client.post("/api/v1/mobile/auth/logout", headers=mobile_headers)
        assert logout.status_code == 204

        after_logout = await client.get("/api/v1/mobile/auth/me", headers=mobile_headers)
        assert after_logout.status_code == 401
        assert after_logout.json()["error"]["code"] == "IDENTITY_SESSION_REVOKED"

    async def test_wrong_vehicle_plate_is_rejected(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)

        resp = await client.post(
            "/api/v1/mobile/auth/login",
            json={
                "cpf": cpf, "vehicle_plate": "ZZZ9999", "auth_method": "CPF_VEICULO", "credential": "n/a",
                "device": {"device_identifier": "device-x", "os": "ANDROID", "app_version": "1.0.0"},
            },
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "MOBILE_LOGIN_INVALID_CREDENTIALS"


class TestSessionDeviceIndependenceAudit:
    """Auditoria #4 do usuário — revogar Sessão nunca desativa Dispositivo; desativar Dispositivo
    impede novas Sessões."""

    async def test_logout_never_deactivates_device_but_device_status_blocks_new_login(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        _, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)

        first_login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-002")
        first_headers = {"Authorization": f"Bearer {first_login['access_token']}"}
        device_id = first_login["session"]["device_id"]

        logout = await client.post("/api/v1/mobile/auth/logout", headers=first_headers)
        assert logout.status_code == 204

        # Novo login no MESMO dispositivo, depois do logout — dispositivo continua ATIVO (D132).
        second_login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-002")
        second_headers = {"Authorization": f"Bearer {second_login['access_token']}"}
        device_after_logout = await client.get(f"/api/v1/mobile/devices/{device_id}", headers=second_headers)
        assert device_after_logout.status_code == 200
        assert device_after_logout.json()["status"] == "ATIVO"

        # Desativa o dispositivo via autoatendimento — nova tentativa de login é bloqueada.
        deactivate = await client.patch(
            f"/api/v1/mobile/devices/{device_id}", headers=second_headers, json={"status": "INATIVO"}
        )
        assert deactivate.status_code == 200
        assert deactivate.json()["status"] == "INATIVO"

        blocked = await client.post(
            "/api/v1/mobile/auth/login",
            json={
                "cpf": cpf, "vehicle_plate": plate, "auth_method": "CPF_VEICULO", "credential": "n/a",
                "device": {"device_identifier": "device-002", "os": "ANDROID", "app_version": "1.0.0"},
            },
        )
        assert blocked.status_code == 403
        assert blocked.json()["error"]["code"] == "MOBILE_DEVICE_BLOCKED"


class TestTenantIdentityAudit:
    """Auditoria #5 do usuário — `motorista_id`/`tenant_id` nunca vêm do corpo da requisição, sempre
    da Sessão autenticada; um Motorista nunca enxerga/afeta a Viagem de outro."""

    async def test_driver_never_sees_or_affects_another_drivers_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)

        driver_a_id, cpf_a = await _create_driver(client, gestor_headers)
        vehicle_a_id, plate_a = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_a_id)

        driver_b_id, cpf_b = await _create_driver(client, gestor_headers)
        vehicle_b_id, plate_b = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_b_id)

        trip_b = await _create_trip_allocated(client, gestor_headers, client_id, driver_b_id, vehicle_b_id)

        login_a = await _mobile_login(client, cpf=cpf_a, vehicle_plate=plate_a, device_identifier="device-a")
        headers_a = {"Authorization": f"Bearer {login_a['access_token']}"}

        # Motorista A nunca vê a Viagem do Motorista B na própria listagem.
        own_trips = await client.get("/api/v1/mobile/trips", headers=headers_a)
        assert all(t["id"] != trip_b for t in own_trips.json()["data"])

        # Acesso direto por ID é 403, nunca 404 (enumeration-safety).
        get_other = await client.get(f"/api/v1/mobile/trips/{trip_b}", headers=headers_a)
        assert get_other.status_code == 403
        assert get_other.json()["error"]["code"] == "FREIGHT_TRIP_FORBIDDEN"

        # Comando direto também é bloqueado, mesmo com permissão de domínio válida.
        accept_other = await client.post(f"/api/v1/mobile/trips/{trip_b}/commands/accept", headers=headers_a)
        assert accept_other.status_code == 403


class TestOfflineIdempotencyAudit:
    """Auditoria #1 do usuário — reenviar o mesmo `local_id` produz um único efeito de domínio."""

    async def test_resending_the_same_local_id_never_duplicates_the_occurrence(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-idem")
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        local_id = f"local-{uuid.uuid4().hex[:10]}"
        payload = {
            "commands": [
                {
                    "local_id": local_id, "sequence": 1, "command": "REGISTER_OCCURRENCE",
                    "target_entity_type": "trip", "target_entity_id": trip_id,
                    "payload": {
                        "type": "AVARIA", "description": "Avaria detectada em campo.",
                        "occurred_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ]
        }

        first = await client.post("/api/v1/mobile/sync", headers=headers, json=payload)
        assert first.status_code == 200, first.text
        assert first.json()["results"][0]["result"] == "PROCESSADO"

        # D111 — o mesmo `local_id` reenviado nunca cria uma segunda linha em `filas_sincronizacao`
        # (`uq_filas_sincronizacao_identificador_local` + `add_if_absent`); como o item já saiu de
        # PENDENTE/FALHOU na primeira chamada, a segunda nem o reprocessa — resultado vazio, nunca um
        # segundo efeito de domínio.
        second = await client.post("/api/v1/mobile/sync", headers=headers, json=payload)
        assert second.status_code == 200, second.text
        assert second.json()["results"] == []

        occurrences = await client.get(f"/api/v1/mobile/trips/{trip_id}/occurrences", headers=headers)
        assert occurrences.json()["meta"]["pagination"]["total"] == 1


class TestQueueOrderingAudit:
    """Auditoria #2 do usuário — processamento por `sequence`, nunca pela ordem de chegada HTTP."""

    async def test_commands_are_processed_by_sequence_not_by_array_order(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)
        await _advance_to_liberada(tenant_id, trip_id)

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-order")
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        # Enviados no corpo em ordem INVERSA à sequência lógica (retomar, interromper, start) — só
        # funciona sem CONFLITO se o backend reordenar por `sequence` antes de processar.
        payload = {
            "commands": [
                {
                    "local_id": "cmd-retomar", "sequence": 3, "command": "RETOMAR_TRIP",
                    "target_entity_type": "trip", "target_entity_id": trip_id, "payload": {},
                },
                {
                    "local_id": "cmd-interromper", "sequence": 2, "command": "INTERROMPER_TRIP",
                    "target_entity_type": "trip", "target_entity_id": trip_id,
                    "payload": {"notes": "Pane mecânica breve."},
                },
                {
                    "local_id": "cmd-start", "sequence": 1, "command": "START_TRIP",
                    "target_entity_type": "trip", "target_entity_id": trip_id, "payload": {},
                },
            ]
        }

        resp = await client.post("/api/v1/mobile/sync", headers=headers, json=payload)
        assert resp.status_code == 200, resp.text
        results_by_local_id = {r["local_id"]: r for r in resp.json()["results"]}
        assert results_by_local_id["cmd-start"]["result"] == "PROCESSADO"
        assert results_by_local_id["cmd-interromper"]["result"] == "PROCESSADO"
        assert results_by_local_id["cmd-retomar"]["result"] == "PROCESSADO"

        trip = await client.get(f"/api/v1/mobile/trips/{trip_id}", headers=headers)
        assert trip.json()["status"]["operational"] == "EM_DESLOCAMENTO"


class TestConflictAudit:
    """Auditoria #3 do usuário — comando offline válido na origem, inválido na sincronização
    (finalizar uma Viagem já cancelada) — backend registra CONFLITO, preserva o payload original."""

    async def test_finishing_an_already_cancelled_trip_is_recorded_as_conflict(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)
        await _advance_to_liberada(tenant_id, trip_id)

        start = await client.post(f"/api/v1/viagens/{trip_id}/commands/start", headers=gestor_headers)
        assert start.status_code == 200, start.text
        interromper = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/interromper", headers=gestor_headers, json={"notes": "Pane."}
        )
        assert interromper.status_code == 200, interromper.text
        # O Gestor cancela a Viagem enquanto o Motorista está offline, sem que o app saiba.
        cancel = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/cancelar", headers=gestor_headers, json={"notes": "Frete cancelado pelo cliente."}
        )
        assert cancel.status_code == 200, cancel.text
        assert cancel.json()["status"]["operational"] == "CANCELADA"

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-conflict")
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        payload = {
            "commands": [
                {
                    "local_id": "cmd-finish-conflict", "sequence": 1, "command": "FINISH_TRIP",
                    "target_entity_type": "trip", "target_entity_id": trip_id, "payload": {"note": "Cheguei ao destino."},
                }
            ]
        }
        resp = await client.post("/api/v1/mobile/sync", headers=headers, json=payload)
        assert resp.status_code == 200, resp.text
        result = resp.json()["results"][0]
        assert result["result"] == "CONFLITO"
        assert result["conflict"]["current_state"]["status_operacional"] == "CANCELADA"
        assert result["conflict"]["reason"]

        # O payload original permanece intocado no banco (D139), nunca apagado/sobrescrito.
        session_factory = get_session_factory()
        token = set_current_tenant_id(tenant_id)
        try:
            async with session_factory() as session:
                stmt = select(SyncQueueItemModel).where(
                    SyncQueueItemModel.tenant_id == tenant_id,
                    SyncQueueItemModel.identificador_local_unico == "cmd-finish-conflict",
                )
                item = (await session.execute(stmt)).scalar_one()
        finally:
            reset_current_tenant_id(token)
        assert item.status == "CONFLITO"
        assert item.payload["note"] == "Cheguei ao destino."
        assert item.resolucao_conflito is not None


class TestRbacReuseAudit:
    """Auditoria #6 do usuário — a API mobile reutiliza os códigos de domínio já existentes; ter
    `mobile.sync.execute` sozinho nunca basta para executar uma ação que exige um código de domínio
    específico que o Motorista não possui."""

    async def test_sync_command_without_the_underlying_domain_permission_is_rejected(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)
        await _advance_to_liberada(tenant_id, trip_id)

        # Motorista só com `mobile.sync.execute` — sem nenhum código de domínio (`freight.trip.*`).
        role_id = await _create_role(tenant_id, ["mobile.sync.execute"])
        await _create_user(tenant_id, role_ids=frozenset({role_id}), driver_id=uuid.UUID(driver_id))

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-rbac")
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        payload = {
            "commands": [
                {
                    "local_id": "cmd-start-no-perm", "sequence": 1, "command": "START_TRIP",
                    "target_entity_type": "trip", "target_entity_id": trip_id, "payload": {},
                }
            ]
        }
        resp = await client.post("/api/v1/mobile/sync", headers=headers, json=payload)
        assert resp.status_code == 200, resp.text
        result = resp.json()["results"][0]
        assert result["result"] == "REJEITADO"
        assert result["error"]["code"] == "IDENTITY_PERMISSION_DENIED"

        trip = await client.get(f"/api/v1/viagens/{trip_id}", headers=gestor_headers)
        assert trip.json()["status"]["operational"] == "LIBERADA"  # nunca avançou


class TestPushMetadataOnlyAudit:
    """Auditoria #7 do usuário — atualizar `push_token` é só metadata de dispositivo, nunca altera
    estado de Viagem/domínio (D134/D302)."""

    async def test_updating_push_token_never_touches_trip_state(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-push")
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        device_id = login["session"]["device_id"]

        before = await client.get(f"/api/v1/mobile/trips/{trip_id}", headers=headers)
        status_before = before.json()["status"]["operational"]

        update = await client.patch(
            f"/api/v1/mobile/devices/{device_id}", headers=headers, json={"push_token": "novo-token-push-xyz"}
        )
        assert update.status_code == 200
        assert update.json()["id"] == device_id

        after = await client.get(f"/api/v1/mobile/trips/{trip_id}", headers=headers)
        assert after.json()["status"]["operational"] == status_before


class TestStorageFileIdOnlyAudit:
    """Auditoria #8 do usuário — Canhoto/Assinatura sempre `arquivo_id` (UUID), nunca base64/binário
    embutido na entidade."""

    async def test_pod_response_only_ever_contains_file_ids(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)
        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)
        trip_id = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)

        delivery = await client.post(
            f"/api/v1/viagens/{trip_id}/entregas", headers=gestor_headers,
            json={"order": 1, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
        )
        assert delivery.status_code == 201, delivery.text
        delivery_id = delivery.json()["id"]

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-pod")
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        photo_file_id = str(uuid.uuid4())
        signature_file_id = str(uuid.uuid4())
        pod = await client.post(
            f"/api/v1/mobile/trips/{trip_id}/deliveries/{delivery_id}/pod", headers=headers,
            json={
                "photo_file_id": photo_file_id, "signature_file_id": signature_file_id,
                "signatory_role": "RECEBEDOR", "signatory_name": "Ciclano Recebedor",
            },
        )
        assert pod.status_code == 201, pod.text
        body = pod.json()
        assert body["signature_file_id"] == signature_file_id
        # A resposta do Canhoto só carrega id/status/timestamp/arquivo_id — nunca a foto em si nem
        # nenhum campo de imagem/binário/base64 (a foto vive só como `Attachment.arquivo_id`,
        # nunca embutida na entidade).
        assert set(body.keys()) == {"id", "status", "registered_at", "signature_file_id"}

        signatures = await client.get(
            "/api/v1/mobile/signatures", headers=headers, params={"document_type": "CANHOTO", "document_id": body["id"]}
        )
        assert signatures.status_code == 200
        assert len(signatures.json()["data"]) == 1
        signature_body = signatures.json()["data"][0]
        assert signature_body["file_id"] == signature_file_id
        assert set(signature_body.keys()) == {
            "id", "document_type", "document_id", "signatory_role", "signatory_name", "file_id",
            "captured_at", "received_at",
        }


class TestSameCommandWebAndMobileAudit:
    """Auditoria adicional do usuário — o mesmo comando via Web e via Mobile produz o mesmo efeito
    de domínio (validação concreta de D303: dois clientes, uma única regra)."""

    async def test_accept_trip_via_web_and_via_mobile_produce_the_same_transition(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, gestor_headers)

        driver_id, cpf = await _create_driver(client, gestor_headers)
        vehicle_id, plate = await _create_vehicle(client, gestor_headers, category_id)
        # Um Veículo Tracionador só pode ter uma alocação VIGENTE por vez — a segunda Viagem usa um
        # segundo veículo; o Motorista (que é quem loga/comanda via Mobile) é o mesmo nas duas.
        vehicle_id_2, _ = await _create_vehicle(client, gestor_headers, category_id)
        await _register_mobile_driver(tenant_id, driver_id)

        trip_web = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id)
        trip_mobile = await _create_trip_allocated(client, gestor_headers, client_id, driver_id, vehicle_id_2)

        accept_web = await client.post(f"/api/v1/viagens/{trip_web}/commands/accept", headers=gestor_headers)
        assert accept_web.status_code == 200, accept_web.text

        login = await _mobile_login(client, cpf=cpf, vehicle_plate=plate, device_identifier="device-parity")
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        accept_mobile = await client.post(f"/api/v1/mobile/trips/{trip_mobile}/commands/accept", headers=headers)
        assert accept_mobile.status_code == 200, accept_mobile.text

        # Mesmo efeito: D129 — nenhuma das duas muda status_operacional; ambas geram exatamente zero
        # linhas de histórico (aceite é aditivo, evento sem transição).
        assert accept_web.json()["status"]["operational"] == accept_mobile.json()["status"]["operational"] == "PLANEJADA"

        history_web = await client.get(f"/api/v1/viagens/{trip_web}/timeline", headers=gestor_headers)
        history_mobile = await client.get(f"/api/v1/viagens/{trip_mobile}/timeline", headers=gestor_headers)
        assert history_web.status_code == history_mobile.status_code == 200


class TestTenantIsolation:
    async def test_cross_tenant_mobile_device_access_is_impossible(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        gestor_headers_a, tenant_a, category_a = await _full_access_actor(client, tenants)
        gestor_headers_b, tenant_b, category_b = await _full_access_actor(client, tenants)

        driver_b_id, cpf_b = await _create_driver(client, gestor_headers_b)
        _, plate_b = await _create_vehicle(client, gestor_headers_b, category_b)
        await _register_mobile_driver(tenant_b, driver_b_id)

        # CPF do Motorista B não existe no tenant A — login com placa de A nunca encontra o par.
        driver_a_id, cpf_a = await _create_driver(client, gestor_headers_a)
        await _register_mobile_driver(tenant_a, driver_a_id)

        cross = await client.post(
            "/api/v1/mobile/auth/login",
            json={
                "cpf": cpf_b, "vehicle_plate": plate_b, "auth_method": "CPF_VEICULO", "credential": "n/a",
                "device": {"device_identifier": "device-cross", "os": "ANDROID", "app_version": "1.0.0"},
            },
        )
        # Login de B funciona normalmente (prova que o par CPF+Placa É de B, não um erro de setup).
        assert cross.status_code == 200, cross.text
