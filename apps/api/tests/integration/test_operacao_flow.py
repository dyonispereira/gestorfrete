from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.infrastructure.persistence.models.cte_model import CteModel, CteStatusHistoryModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
    FiscalConfigurationModel,
)
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.odometer_reading_model import OdometerReadingModel
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.infrastructure.persistence.models.collection_model import CollectionModel
from modules.freight.infrastructure.persistence.models.delivery_model import DeliveryModel, DeliveryWindowModel
from modules.freight.infrastructure.persistence.models.manifest_model import CargoItemModel, ManifestModel
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
from modules.maintenance.infrastructure.persistence.models.checklist_model import (
    ChecklistModel,
    ChecklistStatusHistoryModel,
)
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel
from shared.collaboration.infrastructure.persistence.models.comment_model import CommentModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 5 — Operação/Viagens, o core domain do sistema. D352 aplicado ao agregado
`Trip` e suas entidades internas (`TripAllocation`/`Delivery`/`ProofOfDelivery`/`Occurrence`) mais
as duas auditorias explicitamente pedidas pelo usuário: (1) `encerrada` é `GENERATED`, nunca
escrita pela aplicação; (2) Snapshots (`cliente_snapshot`/`nome_motorista_snapshot`/
`placa_veiculo_snapshot`) permanecem congelados mesmo depois que a fonte muda."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.dispatch", "Despachar viagem", "freight"),
    ("freight.trip.start", "Iniciar viagem", "freight"),
    ("freight.trip.finish", "Finalizar viagem", "freight"),
    ("freight.trip.cancel", "Cancelar viagem", "freight"),
    ("freight.trip.reassign", "Reatribuir recursos da viagem", "freight"),
    ("freight.trip.close", "Encerramento administrativo da viagem", "freight"),
    ("freight.delivery.view", "Ver entregas", "freight"),
    ("freight.delivery.create", "Criar entregas", "freight"),
    ("freight.delivery.edit", "Editar entregas", "freight"),
    ("freight.occurrence.view", "Ver ocorrências", "freight"),
    ("freight.occurrence.create", "Criar ocorrências", "freight"),
    ("freight.occurrence.edit", "Editar ocorrências", "freight"),
    ("freight.pod.create", "Registrar canhoto", "freight"),
    ("freight.pickup.create", "Registrar coleta", "freight"),
    ("freight.packing_list.create", "Criar romaneio", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("crm.client.edit", "Editar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("drivers.driver.edit", "Editar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("maintenance.checklist.view", "Ver checklists", "maintenance"),
    ("maintenance.checklist.fill", "Preencher checklist", "maintenance"),
    ("maintenance.checklist.approve", "Aprovar checklist", "maintenance"),
    ("maintenance.checklist.reject", "Reprovar checklist", "maintenance"),
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


async def _seed_fiscal_configuration(tenant_id: uuid.UUID) -> None:
    """D396 — despachar uma Viagem agora cria um CT-e automaticamente, o que exige uma
    `FiscalConfiguration` (Lote 7) para o tenant. Seed direto via Repository, mesmo padrão de
    `PaymentMethod` (D386) — sem fluxo de Onboarding real neste backend ainda."""

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
    await _seed_fiscal_configuration(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    _, headers = await _login(client, email)
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
        await session.execute(delete(CommentModel).where(CommentModel.tenant_id == tenant_id))
        if entrega_ids:
            await session.execute(delete(ProofOfDeliveryModel).where(ProofOfDeliveryModel.entrega_id.in_(entrega_ids)))
            await session.execute(delete(DeliveryWindowModel).where(DeliveryWindowModel.entrega_id.in_(entrega_ids)))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(CargoItemModel).where(CargoItemModel.tenant_id == tenant_id))
        await session.execute(delete(ManifestModel).where(ManifestModel.tenant_id == tenant_id))
        await session.execute(delete(CollectionModel).where(CollectionModel.tenant_id == tenant_id))
        await session.execute(delete(DeliveryModel).where(DeliveryModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        # D396 — despachar cria um CT-e automaticamente (`ctes.viagem_id` FK); precisa sair antes
        # de `TripModel`.
        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        # Pilot Hardening Final, Parte 6 — checklists.veiculo_tracionador_id FK; precisa sair antes
        # de VehicleModel.
        await session.execute(delete(ChecklistStatusHistoryModel).where(ChecklistStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(ChecklistModel).where(ChecklistModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleImpedimentModel).where(VehicleImpedimentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
        await session.execute(delete(OdometerReadingModel).where(OdometerReadingModel.tenant_id == tenant_id))
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


async def _create_client(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"razao_social": "Cliente de Teste LTDA", "document": f"{uuid.uuid4().int % 10**11:011d}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_driver(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"nome": "Motorista de Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/veiculos",
        headers=headers,
        json={
            "plate": f"VG{uuid.uuid4().hex[:5].upper()}", "renavam": f"{uuid.uuid4().int % 10**11:011d}",
            "fabricante": "Volvo", "modelo": "FH540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _allocate_and_plan(
    client: AsyncClient, headers: dict[str, str], trip_id: str, driver_id: str, vehicle_id: str
) -> None:
    resp = await client.post(
        f"/api/v1/viagens/{trip_id}/resources",
        headers=headers,
        json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
    )
    assert resp.status_code == 201, resp.text


async def _advance_to_em_entrega(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, trip_id: str
) -> None:
    """`RASCUNHO` (com alocação já criada, `PLANEJADA`) até `EM_ENTREGA`. `AGUARDANDO_CHECKLIST→
    LIBERADA` ainda não tem endpoint HTTP (depende do lote de Checklist), então continua simulada
    via `TripInternalTransitions` (D376) — mas `EM_DESLOCAMENTO→CARREGANDO` e `CARREGANDO→
    EM_TRANSITO`/`EM_ENTREGA` passam a usar os comandos HTTP reais (V1 Operational Hardening,
    Parte 2/3): `POST /coletas` e `POST /romaneios`, nunca mais `TripInternalTransitions.
    register_collection`/`confirm_manifest`."""

    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)

    dispatch_resp = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
    assert dispatch_resp.status_code == 200, dispatch_resp.text
    assert dispatch_resp.json()["status"]["operational"] == "EM_DESLOCAMENTO"

    delivery_resp = await client.post(
        f"/api/v1/viagens/{trip_id}/entregas",
        headers=headers,
        json={"order": 1, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
    )
    assert delivery_resp.status_code == 201, delivery_resp.text

    collection_resp = await client.post(
        f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True}
    )
    assert collection_resp.status_code == 201, collection_resp.text
    assert collection_resp.json()["trip_operational_status"] == "CARREGANDO"

    manifest_resp = await client.post(
        f"/api/v1/viagens/{trip_id}/romaneios",
        headers=headers,
        json={
            "document_number": "RM-0001",
            "items": [{"description": "Pallet de caixas", "weight_kg": "120.50", "quantity": 2}],
        },
    )
    assert manifest_resp.status_code == 201, manifest_resp.text
    assert manifest_resp.json()["trip_operational_status"] == "EM_ENTREGA"

    trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
    assert trip_after.json()["status"]["operational"] == "EM_ENTREGA"


class TestTripCreationIdempotency:
    """V1 Operational Hardening, Parte 6 (D211) — prioridade 1 da lista: `POST /viagens` real,
    Redis-backed, não mais só documentado (D418 fechado). `Idempotency-Key` é aceita, não exigida
    (não quebra clientes que ainda não a enviam) — quando enviada, a dedução é real."""

    async def test_same_key_and_payload_never_creates_a_second_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        idempotency_key = str(uuid.uuid4())
        payload = {"cliente_id": client_id}

        first = await client.post(
            "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key}, json=payload
        )
        assert first.status_code == 201, first.text
        trip_id = first.json()["id"]

        second = await client.post(
            "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key}, json=payload
        )
        assert second.status_code == 201, second.text
        assert second.json()["id"] == trip_id  # mesma Viagem, nunca uma segunda

        list_resp = await client.get("/api/v1/viagens", headers=headers)
        matching = [t for t in list_resp.json()["data"] if t["id"] == trip_id]
        assert len(matching) == 1

    async def test_same_key_with_different_payload_is_rejected(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id_a = await _create_client(client, headers)
        client_id_b = await _create_client(client, headers)
        idempotency_key = str(uuid.uuid4())

        first = await client.post(
            "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key},
            json={"cliente_id": client_id_a},
        )
        assert first.status_code == 201, first.text

        second = await client.post(
            "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key},
            json={"cliente_id": client_id_b},
        )
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"

    async def test_without_idempotency_key_each_request_creates_its_own_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        """Comportamento inalterado para clientes que ainda não enviam o header — a dedução real
        não é imposta como pré-condição obrigatória de uso da API."""

        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)

        first = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        second = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] != second.json()["id"]


async def _create_trip_liberada(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, category_id: uuid.UUID
) -> str:
    """Viagem alocada e `LIBERADA` — ponto de partida comum para os testes de idempotência de
    `commands/dispatch`/`coletas`/`romaneios`. `AGUARDANDO_CHECKLIST→LIBERADA` continua simulado
    via `TripInternalTransitions` aqui, mesmo padrão já usado por `_advance_to_em_entrega`."""

    client_id = await _create_client(client, headers)
    driver_id = await _create_driver(client, headers)
    vehicle_id = await _create_vehicle(client, headers, category_id)

    create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    trip_id = create.json()["id"]
    await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)

    return trip_id


class TestOperationalIdempotencyCoverage:
    """Pilot Hardening Final, Parte 6 — extensão da cobertura de idempotência (D211) para o fluxo
    operacional principal: despacho, encerramento, coleta, romaneio e aprovação de checklist. Mesmo
    mecanismo Redis-backed de `TestTripCreationIdempotency`, mesma prova: retry/duplo-clique nunca
    produz um segundo efeito quando `Idempotency-Key` é enviada. Cada teste também confirma, sem a
    chave, que o guard de domínio por trás continua rejeitando a repetição normalmente — a prova de
    que o replay vem do cache, não de o comando passar a tolerar a transição repetida."""

    async def test_dispatch_same_key_and_payload_never_dispatches_twice(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_liberada(client, headers, tenant_id, category_id)
        idempotency_key = str(uuid.uuid4())
        payload = {"departure_odometer_km": "1000.00"}

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch",
            headers={**headers, "Idempotency-Key": idempotency_key}, json=payload,
        )
        assert first.status_code == 200, first.text
        assert first.json()["status"]["operational"] == "EM_DESLOCAMENTO"

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch",
            headers={**headers, "Idempotency-Key": idempotency_key}, json=payload,
        )
        assert second.status_code == 200, second.text
        assert second.json() == first.json()  # mesma resposta, nenhum novo efeito

        without_key = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers, json=payload
        )
        assert without_key.status_code == 409
        assert without_key.json()["error"]["code"] == "FREIGHT_TRIP_INVALID_TRANSITION"

    async def test_finish_same_key_and_payload_never_finishes_twice(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
        await _advance_to_em_entrega(client, headers, tenant_id, trip_id)

        deliveries = await client.get(f"/api/v1/viagens/{trip_id}/entregas", headers=headers)
        delivery_id = deliveries.json()["data"][0]["id"]
        await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
        )

        idempotency_key = str(uuid.uuid4())
        payload = {"arrival_odometer_km": "1500.00"}

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/finish",
            headers={**headers, "Idempotency-Key": idempotency_key}, json=payload,
        )
        assert first.status_code == 200, first.text
        assert first.json()["status"]["operational"] == "FINALIZADA"

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/finish",
            headers={**headers, "Idempotency-Key": idempotency_key}, json=payload,
        )
        assert second.status_code == 200, second.text
        assert second.json() == first.json()

        without_key = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers, json=payload)
        assert without_key.status_code == 409
        assert without_key.json()["error"]["code"] == "FREIGHT_TRIP_INVALID_TRANSITION"

    async def test_collection_same_key_and_payload_never_registers_twice(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_liberada(client, headers, tenant_id, category_id)
        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert dispatch.status_code == 200, dispatch.text

        idempotency_key = str(uuid.uuid4())
        payload = {"cargo_checked": True}

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/coletas", headers={**headers, "Idempotency-Key": idempotency_key},
            json=payload,
        )
        assert first.status_code == 201, first.text
        assert first.json()["trip_operational_status"] == "CARREGANDO"

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/coletas", headers={**headers, "Idempotency-Key": idempotency_key},
            json=payload,
        )
        assert second.status_code == 201, second.text
        assert second.json() == first.json()

        without_key = await client.post(f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json=payload)
        assert without_key.status_code == 409
        assert without_key.json()["error"]["code"] == "FREIGHT_COLLECTION_ALREADY_REGISTERED"

    async def test_manifest_same_key_and_payload_never_confirms_twice(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_liberada(client, headers, tenant_id, category_id)
        await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        await client.post(f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True})

        idempotency_key = str(uuid.uuid4())
        payload = {"items": [{"description": "Pallet", "weight_kg": "50.00", "quantity": 1}]}

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios", headers={**headers, "Idempotency-Key": idempotency_key},
            json=payload,
        )
        assert first.status_code == 201, first.text
        assert first.json()["trip_operational_status"] == "EM_TRANSITO"

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios", headers={**headers, "Idempotency-Key": idempotency_key},
            json=payload,
        )
        assert second.status_code == 201, second.text
        assert second.json() == first.json()

        without_key = await client.post(f"/api/v1/viagens/{trip_id}/romaneios", headers=headers, json=payload)
        assert without_key.status_code == 409
        assert without_key.json()["error"]["code"] == "FREIGHT_MANIFEST_ALREADY_REGISTERED"

    async def test_checklist_approve_same_key_and_payload_never_approves_twice(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        create_checklist = await client.post(
            "/api/v1/checklists", headers=headers,
            json={"type": "MOTORISTA_SAIDA", "reference_type": "VIAGEM", "reference_id": trip_id},
        )
        assert create_checklist.status_code == 201, create_checklist.text
        checklist_id = create_checklist.json()["id"]

        start = await client.post(f"/api/v1/checklists/{checklist_id}/commands/start", headers=headers)
        assert start.status_code == 200, start.text

        submit = await client.post(
            f"/api/v1/checklists/{checklist_id}/commands/submit", headers=headers,
            json={"itens": [{"descricao": "Pneus e estepe", "critico": True, "resposta": True}]},
        )
        assert submit.status_code == 200, submit.text
        assert submit.json()["status"] == "CONCLUIDO"

        idempotency_key = str(uuid.uuid4())

        first = await client.post(
            f"/api/v1/checklists/{checklist_id}/commands/approve",
            headers={**headers, "Idempotency-Key": idempotency_key}, json={},
        )
        assert first.status_code == 200, first.text
        assert first.json()["status"] == "APROVADO"

        second = await client.post(
            f"/api/v1/checklists/{checklist_id}/commands/approve",
            headers={**headers, "Idempotency-Key": idempotency_key}, json={},
        )
        assert second.status_code == 200, second.text
        assert second.json() == first.json()

        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["status"]["operational"] == "LIBERADA"

        without_key = await client.post(
            f"/api/v1/checklists/{checklist_id}/commands/approve", headers=headers, json={}
        )
        assert without_key.status_code == 409
        assert without_key.json()["error"]["code"] == "MAINTENANCE_CHECKLIST_INVALID_TRANSITION"


class TestIdempotencyConcurrency:
    """Pilot Hardening Final, Parte 6 — prova de comportamento sob concorrência real, não só
    sequencial. `IdempotencyStore.reserve` usa `SET NX EX` (atômico no Redis): quando N requisições
    concorrentes chegam com a mesma `Idempotency-Key`, só uma consegue reservar a chave — a garantia
    vem do próprio Redis, não de sorte de agendamento do event loop. As demais esperam
    (`_poll_for_response`) e replicam a resposta da dona, em vez de correr para `run()` também."""

    async def test_concurrent_requests_same_key_and_payload_create_a_single_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        idempotency_key = str(uuid.uuid4())
        payload = {"cliente_id": client_id}

        responses = await asyncio.gather(
            *[
                client.post("/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key}, json=payload)
                for _ in range(5)
            ]
        )
        assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
        ids = {r.json()["id"] for r in responses}
        assert len(ids) == 1  # 5 requisições concorrentes, uma única Viagem

        list_resp = await client.get("/api/v1/viagens", headers=headers)
        matching = [t for t in list_resp.json()["data"] if t["id"] in ids]
        assert len(matching) == 1

    async def test_concurrent_requests_same_key_and_payload_dispatch_a_trip_once(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        """Segundo endpoint provado sob concorrência, não só criação — `dispatch` tem sua própria
        guarda de domínio (`LIBERADA→EM_DESLOCAMENTO`, só uma vez); se o guard de idempotência
        deixasse duas requisições passarem para `run()`, a perdedora bateria nessa guarda e
        voltaria 409 em vez de replicar a resposta da vencedora — as 5 respostas idênticas abaixo
        são a prova de que isso não aconteceu."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_liberada(client, headers, tenant_id, category_id)
        idempotency_key = str(uuid.uuid4())
        payload = {"departure_odometer_km": "1000.00"}

        responses = await asyncio.gather(
            *[
                client.post(
                    f"/api/v1/viagens/{trip_id}/commands/dispatch",
                    headers={**headers, "Idempotency-Key": idempotency_key}, json=payload,
                )
                for _ in range(5)
            ]
        )
        assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
        bodies = [r.json() for r in responses]
        assert all(b == bodies[0] for b in bodies)
        assert bodies[0]["status"]["operational"] == "EM_DESLOCAMENTO"

    async def test_concurrent_requests_same_key_different_payload_never_create_two_trips(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id_a = await _create_client(client, headers)
        client_id_b = await _create_client(client, headers)
        idempotency_key = str(uuid.uuid4())

        responses = await asyncio.gather(
            client.post(
                "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key},
                json={"cliente_id": client_id_a},
            ),
            client.post(
                "/api/v1/viagens", headers={**headers, "Idempotency-Key": idempotency_key},
                json={"cliente_id": client_id_b},
            ),
        )
        statuses = sorted(r.status_code for r in responses)
        assert statuses == [201, 409], [r.text for r in responses]  # uma cria, a outra é rejeitada
        mismatch = next(r for r in responses if r.status_code == 409)
        assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"

        list_resp = await client.get("/api/v1/viagens", headers=headers)
        assert len(list_resp.json()["data"]) == 1  # nunca duas Viagens, mesmo sob concorrência

    async def test_concurrent_requests_same_literal_key_across_tenants_never_collide(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, _, _ = await _full_access_actor(client, tenants)
        client_id_a = await _create_client(client, headers_a)
        client_id_b = await _create_client(client, headers_b)
        idempotency_key = str(uuid.uuid4())  # mesma chave literal, dois tenants diferentes

        responses = await asyncio.gather(
            client.post(
                "/api/v1/viagens", headers={**headers_a, "Idempotency-Key": idempotency_key},
                json={"cliente_id": client_id_a},
            ),
            client.post(
                "/api/v1/viagens", headers={**headers_b, "Idempotency-Key": idempotency_key},
                json={"cliente_id": client_id_b},
            ),
        )
        assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
        assert responses[0].json()["id"] != responses[1].json()["id"]  # sem colisão entre tenants


class TestTripLifecycle:
    async def test_create_get_list_patch_delete(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        assert create.status_code == 201, create.text
        trip_id = create.json()["id"]
        assert create.json()["status"]["operational"] == "RASCUNHO"
        assert create.json()["snapshots"]["client_snapshot"]["razao_social"] == "Cliente de Teste LTDA"

        get_resp = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert get_resp.status_code == 200

        list_resp = await client.get("/api/v1/viagens", headers=headers)
        assert list_resp.status_code == 200
        assert any(t["id"] == trip_id for t in list_resp.json()["data"])

        patch_resp = await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"data_programada": "2026-09-01"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["scheduled_date"] == "2026-09-01"

        delete_resp = await client.delete(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert delete_resp.status_code == 204

        after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert after.status_code == 404  # D343 — soft delete não aparece em consulta normal

        creation_logs = await _logs_for(tenant_id, "viagens", "CRIACAO")
        assert uuid.UUID(trip_id) in creation_logs

    async def test_can_still_delete_while_planejada_but_not_once_awaiting_checklist(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        # D219 — RASCUNHO/PLANEJADA (estados iniciais) ainda permitem exclusão.
        planejada = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert planejada.json()["status"]["operational"] == "PLANEJADA"

        simulator = TripInternalTransitions()
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=datetime.now(timezone.utc))
        finally:
            reset_current_tenant_id(token)

        delete_resp = await client.delete(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert delete_resp.status_code == 422
        assert delete_resp.json()["error"]["code"] == "FREIGHT_TRIP_CANNOT_DELETE_STARTED"

    async def test_tenant_isolation(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, _, _ = await _full_access_actor(client, tenants)
        client_id_b = await _create_client(client, headers_b)

        created = await client.post("/api/v1/viagens", headers=headers_b, json={"cliente_id": client_id_b})
        trip_id = created.json()["id"]

        cross_tenant = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "FREIGHT_TRIP_NOT_FOUND"


class TestTripAllocationFlow:
    async def test_first_allocation_plans_trip_and_reallocate_supersedes_it(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        other_driver_id = await _create_driver(client, headers)
        other_vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]

        allocation = await client.post(
            f"/api/v1/viagens/{trip_id}/resources",
            headers=headers,
            json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
        )
        assert allocation.status_code == 201, allocation.text
        assert allocation.json()["status"] == "VIGENTE"

        # D376 — só RASCUNHO→PLANEJADA acontece aqui; a Viagem descansa observável em PLANEJADA.
        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["status"]["operational"] == "PLANEJADA"
        assert trip_after.json()["references"]["driver_id"] == driver_id

        second_allocation = await client.post(
            f"/api/v1/viagens/{trip_id}/resources",
            headers=headers,
            json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
        )
        assert second_allocation.status_code == 409
        assert second_allocation.json()["error"]["code"] == "FREIGHT_TRIP_ALREADY_HAS_ALLOCATION"

        reallocate = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/reallocate-resources",
            headers=headers,
            json={"driver_id": other_driver_id, "tractor_unit_id": other_vehicle_id, "reason": "Troca de motorista"},
        )
        assert reallocate.status_code == 200, reallocate.text
        assert reallocate.json()["driver_id"] == other_driver_id

        history = await client.get(f"/api/v1/viagens/{trip_id}/resources", headers=headers, params={"history": "true"})
        assert history.status_code == 200
        statuses = {a["id"]: a["status"] for a in history.json()["data"]}
        assert sorted(statuses.values()) == ["SUBSTITUIDA", "VIGENTE"]


class TestTripAllocationLifecycleFlow:
    """V1 Operational Hardening, Parte 1 — a Alocação `VIGENTE` deixa de bloquear o Veículo assim
    que a Viagem dona termina, por qualquer um dos três caminhos que produzem um estado terminal
    (fluxo normal via `commands/finish`, `commands/cancelar`, `commands/close-administrative`).
    Fecha o P0 do Go-Live Audit: antes desta correção, `alocacoes_recurso_viagem` permanecia
    `VIGENTE` para sempre e `exists_vigente_for_vehicle_excluding_trip` bloqueava qualquer nova
    Viagem no mesmo Veículo com `FREIGHT_VEHICLE_UNAVAILABLE`."""

    async def test_finishing_a_trip_ends_its_allocation_and_frees_the_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
        await _advance_to_em_entrega(client, headers, tenant_id, trip_id)

        deliveries = await client.get(f"/api/v1/viagens/{trip_id}/entregas", headers=headers)
        delivery_id = deliveries.json()["data"][0]["id"]
        await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
        )

        finish = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers)
        assert finish.status_code == 200, finish.text

        history = await client.get(
            f"/api/v1/viagens/{trip_id}/resources", headers=headers, params={"history": "true"}
        )
        assert [a["status"] for a in history.json()["data"]] == ["ENCERRADA"]

        await self._assert_vehicle_is_reallocatable(client, headers, vehicle_id)

    async def test_cancelling_a_trip_ends_its_allocation_and_frees_the_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        cancelar = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/cancelar", headers=headers, json={"notes": "Cliente desistiu."}
        )
        assert cancelar.status_code == 200, cancelar.text

        history = await client.get(
            f"/api/v1/viagens/{trip_id}/resources", headers=headers, params={"history": "true"}
        )
        assert [a["status"] for a in history.json()["data"]] == ["ENCERRADA"]

        await self._assert_vehicle_is_reallocatable(client, headers, vehicle_id)

    async def test_closing_a_trip_administratively_ends_its_allocation_and_frees_the_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        close = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/close-administrative",
            headers=headers,
            json={"justification": "Encerramento administrativo — viagem obsoleta."},
        )
        assert close.status_code == 200, close.text

        history = await client.get(
            f"/api/v1/viagens/{trip_id}/resources", headers=headers, params={"history": "true"}
        )
        assert [a["status"] for a in history.json()["data"]] == ["ENCERRADA"]

        await self._assert_vehicle_is_reallocatable(client, headers, vehicle_id)

    async def test_a_still_active_trip_keeps_blocking_double_allocation_of_the_same_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        other_client_id = await _create_client(client, headers)
        other_driver_id = await _create_driver(client, headers)
        second_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": other_client_id})
        second_trip_id = second_trip.json()["id"]

        blocked = await client.post(
            f"/api/v1/viagens/{second_trip_id}/resources",
            headers=headers,
            json={"driver_id": other_driver_id, "tractor_unit_id": vehicle_id},
        )
        assert blocked.status_code == 422
        assert blocked.json()["error"]["code"] == "FREIGHT_VEHICLE_UNAVAILABLE"

    @staticmethod
    async def _assert_vehicle_is_reallocatable(client: AsyncClient, headers: dict[str, str], vehicle_id: str) -> None:
        """Veículo A: cria Viagem 2, aloca o MESMO Veículo A com sucesso — a prova pedida
        explicitamente pelo usuário para os três cenários de encerramento."""

        new_client_id = await _create_client(client, headers)
        new_driver_id = await _create_driver(client, headers)
        new_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": new_client_id})
        new_trip_id = new_trip.json()["id"]

        reallocation = await client.post(
            f"/api/v1/viagens/{new_trip_id}/resources",
            headers=headers,
            json={"driver_id": new_driver_id, "tractor_unit_id": vehicle_id},
        )
        assert reallocation.status_code == 201, reallocation.text
        assert reallocation.json()["status"] == "VIGENTE"
        assert reallocation.json()["tractor_unit_id"] == vehicle_id


class TestTripAcceptFlow:
    async def test_accept_is_idempotent_and_never_changes_status(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        accept = await client.post(f"/api/v1/viagens/{trip_id}/commands/accept", headers=headers)
        assert accept.status_code == 200
        assert accept.json()["status"]["operational"] == "PLANEJADA"

        accept_again = await client.post(f"/api/v1/viagens/{trip_id}/commands/accept", headers=headers)
        assert accept_again.status_code == 409
        assert accept_again.json()["error"]["code"] == "FREIGHT_TRIP_ALREADY_ACCEPTED"


class TestTripInterromperRetomarFlow:
    async def test_interromper_requires_notes_and_retomar_restores_previous_state(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert dispatch.status_code == 200
        assert dispatch.json()["status"]["operational"] == "EM_DESLOCAMENTO"

        missing_notes = await client.post(f"/api/v1/viagens/{trip_id}/commands/interromper", headers=headers, json={"notes": ""})
        assert missing_notes.status_code == 400
        assert missing_notes.json()["error"]["code"] == "FREIGHT_TRIP_NOTES_REQUIRED"

        interromper = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/interromper", headers=headers, json={"notes": "Pane mecânica em rota."}
        )
        assert interromper.status_code == 200, interromper.text
        assert interromper.json()["status"]["operational"] == "INTERROMPIDA"

        retomar = await client.post(f"/api/v1/viagens/{trip_id}/commands/retomar", headers=headers)
        assert retomar.status_code == 200, retomar.text
        assert retomar.json()["status"]["operational"] == "EM_DESLOCAMENTO"


class TestTripCancelarFlow:
    async def test_cancelar_requires_notes(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]

        cancelar = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/cancelar", headers=headers, json={"notes": "Cliente desistiu."}
        )
        assert cancelar.status_code == 200, cancelar.text
        assert cancelar.json()["status"]["operational"] == "CANCELADA"


class TestTripCloseAdministrativeFlow:
    async def test_close_administrative_never_forces_encerrada(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]

        missing_justification = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/close-administrative", headers=headers, json={"justification": ""}
        )
        assert missing_justification.status_code == 400

        close = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/close-administrative",
            headers=headers,
            json={"justification": "Encerramento administrativo — viagem obsoleta."},
        )
        assert close.status_code == 200, close.text
        assert close.json()["status"]["operational"] == "FINALIZADA"
        assert close.json()["status"]["closed"] is False  # D019 — nunca força ENCERRADA


class TestCollectionFlow:
    """V1 Operational Hardening, Parte 2 — `POST /coletas` fecha `EM_DESLOCAMENTO → CARREGANDO`
    (`018-trip-status.md`) usando exatamente `Trip.mark_collected()`, sem novo estado."""

    async def test_registering_collection_moves_trip_to_carregando(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        too_early = await client.post(
            f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True}
        )
        assert too_early.status_code == 409
        assert too_early.json()["error"]["code"] == "FREIGHT_TRIP_INVALID_TRANSITION"

        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert dispatch.status_code == 200, dispatch.text

        collect = await client.post(
            f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True}
        )
        assert collect.status_code == 201, collect.text
        assert collect.json()["trip_operational_status"] == "CARREGANDO"
        assert collect.json()["cargo_checked"] is True

        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["status"]["operational"] == "CARREGANDO"

        duplicate = await client.post(
            f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True}
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "FREIGHT_COLLECTION_ALREADY_REGISTERED"


class TestManifestFlow:
    """V1 Operational Hardening, Parte 2/3 — `POST /romaneios` fecha `CARREGANDO → EM_TRANSITO`
    (com cascata para `EM_ENTREGA` quando já há Entrega `PENDENTE`), usando exatamente
    `Trip.mark_manifest_checked()`. Nenhum novo estado — a mesma máquina já documentada."""

    async def test_manifest_requires_at_least_one_cargo_item(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        await client.post(f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True})

        empty_items = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios", headers=headers, json={"document_number": None, "items": []}
        )
        assert empty_items.status_code == 422
        assert empty_items.json()["error"]["code"] == "FREIGHT_MANIFEST_REQUIRES_CARGO_ITEM"

        invalid_weight = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios",
            headers=headers,
            json={"items": [{"description": "Caixa", "weight_kg": "0", "quantity": 1}]},
        )
        assert invalid_weight.status_code == 422
        assert invalid_weight.json()["error"]["code"] == "FREIGHT_CARGO_ITEM_PESO_INVALIDO"

        ok = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios",
            headers=headers,
            json={"items": [{"description": "Caixa", "weight_kg": "10.00", "quantity": 1}]},
        )
        assert ok.status_code == 201, ok.text
        # Nenhuma Entrega registrada nesta Viagem — cai direto em EM_TRANSITO, nunca EM_ENTREGA.
        assert ok.json()["trip_operational_status"] == "EM_TRANSITO"
        assert len(ok.json()["items"]) == 1

        duplicate = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios",
            headers=headers,
            json={"items": [{"description": "Caixa 2", "weight_kg": "5.00", "quantity": 1}]},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "FREIGHT_MANIFEST_ALREADY_REGISTERED"

    async def test_manifest_cascades_to_em_entrega_when_deliveries_are_pending(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
        await _advance_to_em_entrega(client, headers, tenant_id, trip_id)  # já cobre a cascata em si

        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["status"]["operational"] == "EM_ENTREGA"


class TestDeliveryFlow:
    async def test_full_delivery_and_finish_flow(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
        await _advance_to_em_entrega(client, headers, tenant_id, trip_id)

        deliveries = await client.get(f"/api/v1/viagens/{trip_id}/entregas", headers=headers)
        assert deliveries.status_code == 200
        delivery_id = deliveries.json()["data"][0]["id"]

        duplicate_order = await client.post(
            f"/api/v1/viagens/{trip_id}/entregas",
            headers=headers,
            json={"order": 1, "recipient": "Outro", "delivery_address": {}},
        )
        assert duplicate_order.status_code == 409
        assert duplicate_order.json()["error"]["code"] == "FREIGHT_DELIVERY_ORDER_ALREADY_EXISTS"

        # `commands/finish` exige todas as Entregas em estado terminal + Canhoto registrado.
        finish_too_early = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers)
        assert finish_too_early.status_code == 422
        assert finish_too_early.json()["error"]["code"] == "FREIGHT_TRIP_DELIVERIES_PENDING"

        canhoto = await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        assert canhoto.status_code == 201, canhoto.text
        assert canhoto.json()["status"] == "REGISTRADO"

        duplicate_canhoto = await client.post(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={}
        )
        assert duplicate_canhoto.status_code == 409
        assert duplicate_canhoto.json()["error"]["code"] == "FREIGHT_POD_ALREADY_REGISTERED"

        conclude = await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
        )
        assert conclude.status_code == 200, conclude.text
        assert conclude.json()["status"] == "CONCLUIDA"

        finish = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers)
        assert finish.status_code == 200, finish.text
        assert finish.json()["status"]["operational"] == "FINALIZADA"

    async def test_rejection_requires_reason(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)
        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        delivery_resp = await client.post(
            f"/api/v1/viagens/{trip_id}/entregas",
            headers=headers,
            json={
                "order": 1, "recipient": "Fulano", "delivery_address": {},
                "window": {"starts_at": "2026-09-01T14:00:00Z", "ends_at": "2026-09-01T17:00:00Z"},
            },
        )
        assert delivery_resp.status_code == 201, delivery_resp.text
        assert delivery_resp.json()["window"]["starts_at"] is not None
        delivery_id = delivery_resp.json()["id"]

        rejected = await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "RECUSADA"}
        )
        assert rejected.status_code == 422
        assert rejected.json()["error"]["code"] == "FREIGHT_DELIVERY_REJECTION_REASON_REQUIRED"


class TestOccurrenceFlow:
    async def test_create_list_and_update_occurrence(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]

        occurrence = await client.post(
            f"/api/v1/viagens/{trip_id}/occurrences",
            headers=headers,
            json={
                "type": "AVARIA", "description": "Avaria identificada na conferência.", "severity": "ALTA",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert occurrence.status_code == 201, occurrence.text
        occurrence_id = occurrence.json()["id"]
        assert occurrence.json()["status"] == "ABERTA"

        # Registrar uma Ocorrência não move a Viagem para INTERROMPIDA automaticamente.
        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["status"]["operational"] == "RASCUNHO"

        listed = await client.get(f"/api/v1/viagens/{trip_id}/occurrences", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["meta"]["pagination"]["total"] == 1

        resolved = await client.patch(
            f"/api/v1/viagens/{trip_id}/occurrences/{occurrence_id}", headers=headers, json={"status": "RESOLVIDA"}
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "RESOLVIDA"

        creation_logs = await _logs_for(tenant_id, "ocorrencias", "CRIACAO")
        assert uuid.UUID(occurrence_id) in creation_logs


class TestTimelineFlow:
    async def test_timeline_is_the_union_of_status_history_and_occurrences(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)  # gera 1 STATUS_OPERACIONAL

        await client.post(
            f"/api/v1/viagens/{trip_id}/occurrences",
            headers=headers,
            json={"type": "ATRASO", "description": "SLA de coleta estourado.", "occurred_at": datetime.now(timezone.utc).isoformat()},
        )

        timeline = await client.get(f"/api/v1/viagens/{trip_id}/timeline", headers=headers)
        assert timeline.status_code == 200, timeline.text
        sources = {entry["source"] for entry in timeline.json()["data"]}
        assert "STATUS_OPERACIONAL" in sources
        assert "OCORRENCIA" in sources
        assert "next_cursor" in timeline.json()["meta"]["pagination"]
        assert "total" not in timeline.json()["meta"]["pagination"]  # cursor, nunca offset (D372)


class TestFullOperationalCycleFlow:
    """V1 Operational Hardening, Parte 4 — Encerramento Real. Prova, numa única Viagem e sem
    Encerramento Administrativo, o ciclo operacional completo pedido pelo usuário: despacho com
    hodômetro de saída → Coleta real → Romaneio real → Entrega → Canhoto → `commands/finish` com
    hodômetro de chegada → KM realizado corretamente calculado → Alocação `ENCERRADA` → Veículo
    reutilizável numa segunda Viagem. Complementa (não substitui) a prova e2e "Dia Real da
    Transportadora" — mais rápida, isolada, mesma asserção de fundo."""

    async def test_finish_computes_km_ends_allocation_and_frees_vehicle_for_a_new_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        dispatch = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers,
            json={"departure_odometer_km": "100000.00"},
        )
        assert dispatch.status_code == 200, dispatch.text

        delivery_resp = await client.post(
            f"/api/v1/viagens/{trip_id}/entregas", headers=headers,
            json={"order": 1, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
        )
        delivery_id = delivery_resp.json()["id"]

        collect = await client.post(f"/api/v1/viagens/{trip_id}/coletas", headers=headers, json={"cargo_checked": True})
        assert collect.status_code == 201, collect.text

        manifest = await client.post(
            f"/api/v1/viagens/{trip_id}/romaneios", headers=headers,
            json={"items": [{"description": "Pallet", "weight_kg": "300.00", "quantity": 4}]},
        )
        assert manifest.status_code == 201, manifest.text
        assert manifest.json()["trip_operational_status"] == "EM_ENTREGA"

        await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
        )

        finish = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers,
            json={"arrival_odometer_km": "100350.50"},
        )
        assert finish.status_code == 200, finish.text
        assert finish.json()["status"]["operational"] == "FINALIZADA"

        # `km_rodado` é gravado por um efeito pós-commit (`TripOdometerRecorder`/
        # `TripInternalTransitions.update_km_rodado`) — a resposta do próprio `finish` ainda não o
        # reflete; um GET seguinte já mostra o valor calculado corretamente.
        trip_after_finish = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_finish.json()["distance_traveled_km"] == "350.50"

        allocation_history = await client.get(
            f"/api/v1/viagens/{trip_id}/resources", headers=headers, params={"history": "true"}
        )
        assert [a["status"] for a in allocation_history.json()["data"]] == ["ENCERRADA"]

        second_client_id = await _create_client(client, headers)
        second_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": second_client_id})
        second_driver_id = await _create_driver(client, headers)

        reallocate_same_vehicle = await client.post(
            f"/api/v1/viagens/{second_trip.json()['id']}/resources",
            headers=headers,
            json={"driver_id": second_driver_id, "tractor_unit_id": vehicle_id},
        )
        assert reallocate_same_vehicle.status_code == 201, reallocate_same_vehicle.text


class TestEncerradaAudit:
    """Auditoria dedicada pedida explicitamente pelo usuário — `encerrada` é `GENERATED`, a
    aplicação nunca escreve nela, e qualquer tentativa de escrita direta falha."""

    async def test_direct_write_to_encerrada_fails(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]

        session_factory = get_session_factory()
        async with session_factory() as session:
            with pytest.raises(Exception) as exc_info:
                await session.execute(text("UPDATE viagens SET encerrada = true WHERE id = :id"), {"id": trip_id})
                await session.commit()
            # Postgres rejects any direct write to a GENERATED ALWAYS column (SQLSTATE 428C9) —
            # locale-independent: the column name itself appears in the error either way.
            assert "encerrada" in str(exc_info.value).lower()
            await session.rollback()

    async def test_encerrada_becomes_true_only_after_all_three_dimensions_converge(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
        await _advance_to_em_entrega(client, headers, tenant_id, trip_id)

        deliveries = await client.get(f"/api/v1/viagens/{trip_id}/entregas", headers=headers)
        delivery_id = deliveries.json()["data"][0]["id"]
        await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        await client.patch(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"})

        finish = await client.post(f"/api/v1/viagens/{trip_id}/commands/finish", headers=headers)
        assert finish.status_code == 200, finish.text
        assert finish.json()["status"]["operational"] == "FINALIZADA"
        assert finish.json()["status"]["closed"] is False  # só Operacional convergiu até aqui

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.record_fiscal_transition(trip_id=uuid.UUID(trip_id), status=TripFiscalStatus.MDFE_ENCERRADO, now=now)
        finally:
            reset_current_tenant_id(token)

        still_not_closed = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert still_not_closed.json()["status"]["closed"] is False  # Financeiro ainda não convergiu

        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.record_financial_transition(trip_id=uuid.UUID(trip_id), status=TripFinancialStatus.RECEBIDA, now=now)
        finally:
            reset_current_tenant_id(token)

        finally_closed = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert finally_closed.json()["status"]["closed"] is True
        assert finally_closed.json()["status"]["fiscal"] == "MDFE_ENCERRADO"
        assert finally_closed.json()["status"]["financial"] == "RECEBIDA"


class TestSnapshotAudit:
    """Auditoria dedicada pedida explicitamente pelo usuário — criar Viagem, alterar Cliente/
    Motorista depois, consultar a Viagem, provar que os snapshots continuam exatamente iguais ao
    momento em que foram capturados (D038/D071/D073/D378)."""

    async def test_snapshots_never_resync_after_source_changes(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create.json()["id"]
        assert create.json()["snapshots"]["client_snapshot"]["razao_social"] == "Cliente de Teste LTDA"

        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert dispatch.status_code == 200, dispatch.text
        frozen_driver_name = dispatch.json()["snapshots"]["driver_name_snapshot"]
        frozen_vehicle_plate = dispatch.json()["snapshots"]["tractor_unit_plate_snapshot"]
        frozen_client_snapshot = dispatch.json()["snapshots"]["client_snapshot"]
        assert frozen_driver_name == "Motorista de Teste"

        # Altera as fontes de origem via seus próprios módulos, depois que os snapshots já foram
        # congelados — nenhuma das duas mudanças pode aparecer de volta na Viagem.
        rename_client = await client.patch(
            f"/api/v1/clients/{client_id}", headers=headers, json={"razao_social": "Cliente Renomeado LTDA"}
        )
        assert rename_client.status_code == 200

        rename_driver = await client.patch(
            f"/api/v1/drivers/{driver_id}", headers=headers, json={"nome": "Motorista Renomeado"}
        )
        assert rename_driver.status_code == 200

        trip_after = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after.json()["snapshots"]["driver_name_snapshot"] == frozen_driver_name
        assert trip_after.json()["snapshots"]["tractor_unit_plate_snapshot"] == frozen_vehicle_plate
        assert trip_after.json()["snapshots"]["client_snapshot"] == frozen_client_snapshot
        assert trip_after.json()["snapshots"]["driver_name_snapshot"] != "Motorista Renomeado"
        assert trip_after.json()["snapshots"]["client_snapshot"]["razao_social"] != "Cliente Renomeado LTDA"
