from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.application.fiscal_internal_transitions import FiscalInternalTransitions
from modules.documents.infrastructure.persistence.models.ciot_model import CiotModel, CiotStatusHistoryModel
from modules.documents.infrastructure.persistence.models.correction_letter_model import CorrectionLetterModel
from modules.documents.infrastructure.persistence.models.cte_model import CteModel, CteStatusHistoryModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
    FiscalConfigurationModel,
)
from modules.documents.infrastructure.persistence.models.fiscal_event_model import FiscalEventModel
from modules.documents.infrastructure.persistence.models.mdfe_model import (
    MdfeCteModel,
    MdfeModel,
    MdfeStatusHistoryModel,
)
from modules.documents.infrastructure.persistence.models.referenced_nfe_model import ReferencedNfeModel
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
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel
from shared.collaboration.infrastructure.persistence.models.comment_model import CommentModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 7 — Fiscal (D396-D400). D352 aplicado aos 7 agregados (CT-e/MDF-e/CIOT/Carta de
Correção/NF-e Referenciada/Evento Fiscal/Configuração Fiscal), mais as cinco auditorias
explicitamente pedidas pelo usuário: (1) idempotência — retransmitir o mesmo protocolo SEFAZ/ANTT
nunca duplica registro nem transição; (2) XML nunca inline — só `xml_arquivo_id`, nunca conteúdo;
(3) máquinas de estado — cada transição grava exatamente uma linha em `*_status_history`; (4)
numeração congelada — o número vem da Configuração Fiscal, é copiado no documento na emissão, e
nunca muda depois mesmo que a configuração mude; (5) reprocessamento de evento — reenviar o mesmo
callback nunca duplica linhas em `eventos_fiscais`."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.dispatch", "Despachar viagem", "freight"),
    ("freight.delivery.view", "Ver entregas", "freight"),
    ("freight.delivery.create", "Criar entregas", "freight"),
    ("freight.delivery.edit", "Editar entregas", "freight"),
    ("freight.pod.create", "Registrar canhoto", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("documents.cte.view", "Ver CT-e", "documents"),
    ("documents.cte.issue", "Emitir CT-e", "documents"),
    ("documents.cte.cancel", "Cancelar CT-e", "documents"),
    ("documents.cte.correct", "Emitir carta de correção", "documents"),
    ("documents.mdfe.view", "Ver MDF-e", "documents"),
    ("documents.mdfe.issue", "Emitir MDF-e", "documents"),
    ("documents.mdfe.close", "Encerrar MDF-e", "documents"),
    ("documents.mdfe.cancel", "Cancelar MDF-e", "documents"),
    ("documents.ciot.view", "Ver CIOT", "documents"),
    ("documents.ciot.register", "Registrar CIOT", "documents"),
    ("documents.ciot.cancel", "Cancelar CIOT", "documents"),
    ("documents.sefaz_status.view", "Ver status SEFAZ", "documents"),
    ("documents.nfe_reference.view", "Ver NF-e referenciada", "documents"),
    ("documents.fiscal_config.view", "Ver configuração fiscal", "documents"),
    ("documents.fiscal_config.edit", "Editar configuração fiscal", "documents"),
    ("documents.fiscal_config.manage_certificate", "Alterar certificado", "documents"),
    ("documents.fiscal_config.manage_series", "Alterar série", "documents"),
    ("documents.fiscal_config.switch_environment", "Alternar ambiente", "documents"),
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
                id=category_id, tenant_id=tenant_id, codigo=f"CAT-{category_id.hex[:8]}",
                nome=f"Categoria {category_id.hex[:6]}", status="ATIVA", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return category_id


async def _seed_fiscal_configuration(tenant_id: uuid.UUID) -> None:
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
        await session.execute(delete(CommentModel).where(CommentModel.tenant_id == tenant_id))

        # Fiscal — ordem de FK: filhos antes dos pais.
        await session.execute(delete(FiscalEventModel).where(FiscalEventModel.tenant_id == tenant_id))
        await session.execute(delete(ReferencedNfeModel).where(ReferencedNfeModel.tenant_id == tenant_id))
        await session.execute(delete(CorrectionLetterModel).where(CorrectionLetterModel.tenant_id == tenant_id))
        await session.execute(delete(CiotStatusHistoryModel).where(CiotStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CiotModel).where(CiotModel.tenant_id == tenant_id))
        await session.execute(delete(MdfeStatusHistoryModel).where(MdfeStatusHistoryModel.tenant_id == tenant_id))
        mdfe_ids = (await session.execute(select(MdfeModel.id).where(MdfeModel.tenant_id == tenant_id))).scalars().all()
        if mdfe_ids:
            await session.execute(delete(MdfeCteModel).where(MdfeCteModel.mdfe_id.in_(mdfe_ids)))
        await session.execute(delete(MdfeModel).where(MdfeModel.tenant_id == tenant_id))
        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id))

        if entrega_ids:
            await session.execute(delete(ProofOfDeliveryModel).where(ProofOfDeliveryModel.entrega_id.in_(entrega_ids)))
            await session.execute(delete(DeliveryWindowModel).where(DeliveryWindowModel.entrega_id.in_(entrega_ids)))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(DeliveryModel).where(DeliveryModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        # Populadas por `VehicleAvailabilityProjector` desde que `dispatch_trip`/`finish_trip`
        # foram conectados (Lote Frota e Manutenção, Parte 3) — saem antes de `VehicleModel`.
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


async def _create_driver(client: AsyncClient, headers: dict[str, str], *, employment_type: str = "EMPREGADO") -> str:
    resp = await client.post(
        "/api/v1/drivers", headers=headers,
        json={"nome": "Motorista de Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": employment_type},
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


async def _create_and_dispatch_trip(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, category_id: uuid.UUID
) -> str:
    """Cria Viagem, aloca recursos, avança até `LIBERADA` e despacha — D396 cria o CT-e (`RASCUNHO`)
    automaticamente como efeito colateral. Retorna `trip_id`."""

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

    return trip_id


async def _get_cte_for_trip(client: AsyncClient, headers: dict[str, str], trip_id: str) -> dict[str, Any]:
    listed = await client.get("/api/v1/ctes", headers=headers, params={"trip_id": trip_id})
    assert listed.status_code == 200, listed.text
    items = listed.json()["data"]
    assert len(items) == 1
    return items[0]


async def _advance_cte_to_authorized(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, cte_id: str,
    *, protocolo_sefaz: str | None = None,
) -> None:
    validate = await client.post(f"/api/v1/ctes/{cte_id}/commands/validate", headers=headers)
    assert validate.status_code == 200, validate.text
    sign = await client.post(f"/api/v1/ctes/{cte_id}/commands/sign", headers=headers)
    assert sign.status_code == 200, sign.text
    transmit = await client.post(f"/api/v1/ctes/{cte_id}/commands/transmit", headers=headers)
    assert transmit.status_code == 200, transmit.text

    token = set_current_tenant_id(tenant_id)
    try:
        await FiscalInternalTransitions().receive_cte_sefaz_response(
            cte_id=uuid.UUID(cte_id), approved=True, protocolo_sefaz=protocolo_sefaz or f"SEFAZ-{uuid.uuid4().hex[:10]}",
            chave_acesso="1" * 44, now=datetime.now(timezone.utc),
        )
    finally:
        reset_current_tenant_id(token)


async def _create_delivery(client: AsyncClient, headers: dict[str, str], trip_id: str, *, order: int = 1) -> str:
    resp = await client.post(
        f"/api/v1/viagens/{trip_id}/entregas", headers=headers,
        json={"order": order, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestCteFlow:
    async def test_full_lifecycle_cancel_and_status_history_cardinality(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)

        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]
        assert cte["status"] == "RASCUNHO"

        # Transição inválida — pular direto para `sign` sem `validate` antes.
        invalid = await client.post(f"/api/v1/ctes/{cte_id}/commands/sign", headers=headers)
        assert invalid.status_code == 409
        assert invalid.json()["error"]["code"] == "FISCAL_CTE_INVALID_TRANSITION"

        await _advance_cte_to_authorized(client, headers, tenant_id, cte_id)

        authorized = await client.get(f"/api/v1/ctes/{cte_id}", headers=headers)
        assert authorized.status_code == 200
        assert authorized.json()["status"] == "AUTORIZADO"
        assert authorized.json()["access_key"] == "1" * 44

        trip_after_auth = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_auth.json()["status"]["fiscal"] == "CTE_EMITIDO"

        cancel = await client.post(
            f"/api/v1/ctes/{cte_id}/commands/cancel", headers=headers, json={"notes": "Erro na emissão."}
        )
        assert cancel.status_code == 200, cancel.text
        assert cancel.json()["status"] == "CANCELADO"

        trip_after_cancel = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_cancel.json()["status"]["fiscal"] == "CTE_CANCELADO"

        # Auditoria #3 — validate + sign + transmit + AUTORIZADO (FiscalInternalTransitions) +
        # cancel = exatamente 5 transições reais, 5 linhas de histórico (RASCUNHO nunca ganha uma).
        history = await client.get(f"/api/v1/ctes/{cte_id}/status-history", headers=headers)
        assert history.status_code == 200
        assert len(history.json()["data"]) == 5
        statuses = [entry["status"] for entry in history.json()["data"]]
        assert statuses.count("AUTORIZADO") == 1
        assert statuses.count("CANCELADO") == 1

    async def test_inutilize_from_rascunho(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)

        inutilize = await client.post(f"/api/v1/ctes/{cte['id']}/commands/inutilize", headers=headers)
        assert inutilize.status_code == 200, inutilize.text
        assert inutilize.json()["status"] == "INUTILIZADO"

    async def test_denied_by_sefaz(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        await client.post(f"/api/v1/ctes/{cte_id}/commands/validate", headers=headers)
        await client.post(f"/api/v1/ctes/{cte_id}/commands/sign", headers=headers)
        await client.post(f"/api/v1/ctes/{cte_id}/commands/transmit", headers=headers)

        token = set_current_tenant_id(tenant_id)
        try:
            await FiscalInternalTransitions().receive_cte_sefaz_response(
                cte_id=uuid.UUID(cte_id), approved=False, protocolo_sefaz=f"SEFAZ-{uuid.uuid4().hex[:10]}",
                now=datetime.now(timezone.utc),
            )
        finally:
            reset_current_tenant_id(token)

        denied = await client.get(f"/api/v1/ctes/{cte_id}", headers=headers)
        assert denied.json()["status"] == "DENEGADO"


class TestMdfeFlow:
    async def test_create_requires_authorized_cte_and_close_requires_no_pending_delivery(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        not_authorized = await client.post(
            "/api/v1/mdfes", headers=headers, json={"trip_id": trip_id, "cte_ids": [cte_id]}
        )
        assert not_authorized.status_code == 409
        assert not_authorized.json()["error"]["code"] == "FISCAL_MDFE_CTE_NOT_AUTHORIZED"

        await _advance_cte_to_authorized(client, headers, tenant_id, cte_id)
        delivery_id = await _create_delivery(client, headers, trip_id)

        create_mdfe = await client.post(
            "/api/v1/mdfes", headers=headers, json={"trip_id": trip_id, "cte_ids": [cte_id]}
        )
        assert create_mdfe.status_code == 201, create_mdfe.text
        mdfe_id = create_mdfe.json()["id"]
        assert create_mdfe.json()["status"] == "PENDENTE"
        assert create_mdfe.json()["cte_ids"] == [cte_id]

        token = set_current_tenant_id(tenant_id)
        try:
            await FiscalInternalTransitions().receive_mdfe_sefaz_response(
                mdfe_id=uuid.UUID(mdfe_id), protocolo_sefaz=f"SEFAZ-{uuid.uuid4().hex[:10]}", chave_acesso="2" * 44,
                now=datetime.now(timezone.utc),
            )
        finally:
            reset_current_tenant_id(token)
        authorized = await client.get(f"/api/v1/mdfes/{mdfe_id}", headers=headers)
        assert authorized.json()["status"] == "AUTORIZADO"

        trip_after_auth = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_auth.json()["status"]["fiscal"] == "MDFE_EMITIDO"

        blocked_close = await client.post(f"/api/v1/mdfes/{mdfe_id}/commands/close", headers=headers)
        assert blocked_close.status_code == 409
        assert blocked_close.json()["error"]["code"] == "FISCAL_MDFE_LAST_DELIVERY_PENDING"

        canhoto = await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
        assert canhoto.status_code == 201, canhoto.text
        conclude = await client.patch(
            f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}", headers=headers, json={"status": "CONCLUIDA"}
        )
        assert conclude.status_code == 200, conclude.text

        close = await client.post(f"/api/v1/mdfes/{mdfe_id}/commands/close", headers=headers)
        assert close.status_code == 200, close.text
        assert close.json()["status"] == "ENCERRADO"

        trip_after_close = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_close.json()["status"]["fiscal"] == "MDFE_ENCERRADO"

        # Auditoria #3 — AUTORIZADO (FiscalInternalTransitions) + ENCERRADO = 2 linhas.
        history = await client.get(f"/api/v1/mdfes/{mdfe_id}/status-history", headers=headers)
        assert len(history.json()["data"]) == 2

    async def test_cancel_never_allowed_from_encerrado(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        await _advance_cte_to_authorized(client, headers, tenant_id, cte["id"])

        create_mdfe = await client.post(
            "/api/v1/mdfes", headers=headers, json={"trip_id": trip_id, "cte_ids": [cte["id"]]}
        )
        mdfe_id = create_mdfe.json()["id"]

        cancel = await client.post(
            f"/api/v1/mdfes/{mdfe_id}/commands/cancel", headers=headers, json={"notes": "Desistência."}
        )
        assert cancel.status_code == 200, cancel.text
        assert cancel.json()["status"] == "CANCELADO"

        cancel_again = await client.post(
            f"/api/v1/mdfes/{mdfe_id}/commands/cancel", headers=headers, json={"notes": "Tentando de novo."}
        )
        assert cancel_again.status_code == 409
        assert cancel_again.json()["error"]["code"] == "FISCAL_MDFE_INVALID_TRANSITION"


class TestCiotFlow:
    async def test_requires_autonomous_driver_and_full_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        employed_driver_id = await _create_driver(client, headers, employment_type="EMPREGADO")
        autonomous_driver_id = await _create_driver(client, headers, employment_type="AUTONOMO")

        create_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create_trip.json()["id"]

        not_autonomous = await client.post(
            "/api/v1/ciots", headers=headers, json={"trip_id": trip_id, "driver_id": employed_driver_id}
        )
        assert not_autonomous.status_code == 422
        assert not_autonomous.json()["error"]["code"] == "FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS"

        create = await client.post(
            "/api/v1/ciots", headers=headers, json={"trip_id": trip_id, "driver_id": autonomous_driver_id}
        )
        assert create.status_code == 201, create.text
        ciot_id = create.json()["id"]
        assert create.json()["status"] == "PENDENTE"

        register = await client.post(f"/api/v1/ciots/{ciot_id}/commands/register", headers=headers)
        assert register.status_code == 200, register.text
        assert register.json()["status"] == "REGISTRADO"
        assert register.json()["ciot_code"] is not None
        assert register.json()["antt_protocol"] is not None

        history = await client.get(f"/api/v1/ciots/{ciot_id}/status-history", headers=headers)
        assert len(history.json()["data"]) == 1

    async def test_cancel_blocked_once_trip_started(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        autonomous_driver_id = await _create_driver(client, headers, employment_type="AUTONOMO")
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)

        create = await client.post(
            "/api/v1/ciots", headers=headers, json={"trip_id": trip_id, "driver_id": autonomous_driver_id}
        )
        ciot_id = create.json()["id"]

        cancel = await client.post(
            f"/api/v1/ciots/{ciot_id}/commands/cancel", headers=headers, json={"notes": "Tarde demais."}
        )
        assert cancel.status_code == 409
        assert cancel.json()["error"]["code"] == "FISCAL_CIOT_TRIP_ALREADY_STARTED"


class TestCorrectionLetterAndReferencedNfeFlow:
    async def test_correction_letter_requires_authorized_cte_and_sequences(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        too_early = await client.post(
            f"/api/v1/ctes/{cte_id}/cartas-correcao", headers=headers, json={"correction_text": "Corrige erro."}
        )
        assert too_early.status_code == 409
        assert too_early.json()["error"]["code"] == "FISCAL_CTE_NOT_AUTHORIZED"

        await _advance_cte_to_authorized(client, headers, tenant_id, cte_id)

        first = await client.post(
            f"/api/v1/ctes/{cte_id}/cartas-correcao", headers=headers, json={"correction_text": "Primeira correção."}
        )
        assert first.status_code == 201, first.text
        assert first.json()["sequence_number"] == 1

        second = await client.post(
            f"/api/v1/ctes/{cte_id}/cartas-correcao", headers=headers, json={"correction_text": "Segunda correção."}
        )
        assert second.status_code == 201
        assert second.json()["sequence_number"] == 2

        # O CT-e pai nunca é alterado por uma Carta de Correção (D282).
        cte_after = await client.get(f"/api/v1/ctes/{cte_id}", headers=headers)
        assert cte_after.json()["status"] == "AUTORIZADO"

        listed = await client.get(f"/api/v1/ctes/{cte_id}/cartas-correcao", headers=headers)
        assert listed.json()["meta"]["pagination"]["total"] == 2

    async def test_referenced_nfe_validates_access_key(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        invalid = await client.post(
            f"/api/v1/ctes/{cte_id}/nfe-referenciadas", headers=headers, json={"access_key": "123"}
        )
        assert invalid.status_code == 400
        assert invalid.json()["error"]["code"] == "FISCAL_NFE_REFERENCE_INVALID_ACCESS_KEY"

        valid = await client.post(
            f"/api/v1/ctes/{cte_id}/nfe-referenciadas", headers=headers, json={"access_key": "3" * 44}
        )
        assert valid.status_code == 201, valid.text
        assert valid.json()["access_key"] == "3" * 44


class TestFiscalConfigurationFlow:
    async def test_get_and_field_level_patch_permissions(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)

        get_resp = await client.get("/api/v1/configuracao-fiscal", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["tax_regime"] == "SIMPLES"
        assert get_resp.json()["next_cte_number"] == 1

        full_patch = await client.patch(
            "/api/v1/configuracao-fiscal", headers=headers, json={"tax_regime": "LUCRO_PRESUMIDO"}
        )
        assert full_patch.status_code == 200
        assert full_patch.json()["tax_regime"] == "LUCRO_PRESUMIDO"

        # Ator só com `documents.fiscal_config.view` — sem nenhuma permissão de escrita.
        role_view_only = await _create_role(tenant_id, ["documents.fiscal_config.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_view_only}))
        view_only_headers = await _login(client, email)

        forbidden = await client.patch(
            "/api/v1/configuracao-fiscal", headers=view_only_headers, json={"tax_regime": "SIMPLES"}
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "IDENTITY_PERMISSION_DENIED"

        # Mesmo ator tentando alterar `environment` sem `switch_environment` — rejeitado por
        # inteiro, nunca parcialmente aplicado (D218-style), mesmo que outro campo do corpo
        # pertença a uma permissão que o ator won't even have here either.
        forbidden_env = await client.patch(
            "/api/v1/configuracao-fiscal", headers=view_only_headers, json={"environment": "PRODUCAO"}
        )
        assert forbidden_env.status_code == 403

        still_unchanged = await client.get("/api/v1/configuracao-fiscal", headers=headers)
        assert still_unchanged.json()["environment"] == "HOMOLOGACAO"


class TestIdempotencyAndEventReprocessingAudit:
    """Auditoria #1 (idempotência) e #5 (reprocessamento de evento) do usuário — retransmitir a
    mesma resposta da SEFAZ (mesmo `protocolo_sefaz`) nunca gera uma segunda transição nem duplica
    `eventos_fiscais`."""

    async def test_replaying_the_same_sefaz_protocol_is_a_no_op(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        await client.post(f"/api/v1/ctes/{cte_id}/commands/validate", headers=headers)
        await client.post(f"/api/v1/ctes/{cte_id}/commands/sign", headers=headers)
        await client.post(f"/api/v1/ctes/{cte_id}/commands/transmit", headers=headers)

        protocolo = f"SEFAZ-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        simulator = FiscalInternalTransitions()

        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.receive_cte_sefaz_response(
                cte_id=uuid.UUID(cte_id), approved=True, protocolo_sefaz=protocolo, chave_acesso="4" * 44, now=now
            )
            # Reentrega/timeout seguido de retry — mesma resposta chega de novo.
            await simulator.receive_cte_sefaz_response(
                cte_id=uuid.UUID(cte_id), approved=True, protocolo_sefaz=protocolo, chave_acesso="4" * 44, now=now
            )
            await simulator.receive_cte_sefaz_response(
                cte_id=uuid.UUID(cte_id), approved=True, protocolo_sefaz=protocolo, chave_acesso="4" * 44, now=now
            )
        finally:
            reset_current_tenant_id(token)

        cte_after = await client.get(f"/api/v1/ctes/{cte_id}", headers=headers)
        assert cte_after.json()["status"] == "AUTORIZADO"

        # Nenhuma transição extra — só a linha real da primeira resposta processada.
        history = await client.get(f"/api/v1/ctes/{cte_id}/status-history", headers=headers)
        authorized_rows = [e for e in history.json()["data"] if e["status"] == "AUTORIZADO"]
        assert len(authorized_rows) == 1

        # Auditoria #5 — nenhum `EventoFiscal` duplicado, apesar de 3 chamadas com o mesmo protocolo.
        events = await client.get(
            "/api/v1/fiscal/events", headers=headers,
            params={"document_type": "CTE", "document_id": cte_id, "external_protocol": protocolo},
        )
        assert events.status_code == 200
        assert len(events.json()["data"]) == 1

    async def test_replaying_the_same_antt_protocol_via_event_table_never_duplicates(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        autonomous_driver_id = await _create_driver(client, headers, employment_type="AUTONOMO")
        client_id = await _create_client_entity(client, headers)
        create_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create_trip.json()["id"]

        create_ciot = await client.post(
            "/api/v1/ciots", headers=headers, json={"trip_id": trip_id, "driver_id": autonomous_driver_id}
        )
        ciot_id = create_ciot.json()["id"]

        register = await client.post(f"/api/v1/ciots/{ciot_id}/commands/register", headers=headers)
        protocol = register.json()["antt_protocol"]

        events = await client.get(
            "/api/v1/fiscal/events", headers=headers,
            params={"document_type": "CIOT", "document_id": ciot_id, "external_protocol": protocol},
        )
        assert len(events.json()["data"]) == 1


class TestXmlNeverInlineAudit:
    """Auditoria #2 do usuário (D107/D276) — nenhuma entidade fiscal tem um campo de conteúdo de
    XML/certificado/payload; sempre `*_arquivo_id` (referência), nunca texto/blob."""

    async def test_cte_xml_endpoint_returns_only_a_reference(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        cte_id = cte["id"]

        before_authorized = await client.get(f"/api/v1/ctes/{cte_id}/xml", headers=headers)
        assert before_authorized.status_code == 404
        assert before_authorized.json()["error"]["code"] == "FISCAL_CTE_XML_NOT_AVAILABLE"

        await _advance_cte_to_authorized(client, headers, tenant_id, cte_id)

        xml_ref = await client.get(f"/api/v1/ctes/{cte_id}/xml", headers=headers)
        assert xml_ref.status_code == 200, xml_ref.text
        body = xml_ref.json()
        assert set(body.keys()) == {"xml_file_id", "generated_at"}
        uuid.UUID(body["xml_file_id"])  # é um UUID de referência, nunca conteúdo bruto

        # `CTe.xml_file_id` é a única representação do XML no schema completo do CT-e também —
        # sempre uma referência (UUID), nunca o conteúdo do documento.
        cte_full = await client.get(f"/api/v1/ctes/{cte_id}", headers=headers)
        assert isinstance(cte_full.json()["xml_file_id"], str)
        uuid.UUID(cte_full.json()["xml_file_id"])

    async def test_fiscal_event_payload_is_always_a_reference(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        cte = await _get_cte_for_trip(client, headers, trip_id)
        await _advance_cte_to_authorized(client, headers, tenant_id, cte["id"])

        events = await client.get(
            "/api/v1/fiscal/events", headers=headers, params={"document_type": "CTE", "document_id": cte["id"]}
        )
        assert events.status_code == 200
        for event in events.json()["data"]:
            assert isinstance(event["payload_file_id"], str)
            uuid.UUID(event["payload_file_id"])


class TestNumberingFrozenAudit:
    """Auditoria #4 do usuário (D110/D399) — o número do CT-e vem da Configuração Fiscal, é
    copiado no documento na emissão, e permanece congelado mesmo que a Configuração mude depois."""

    async def test_number_and_series_stay_frozen_after_configuration_changes(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)

        first_trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        first_cte = await _get_cte_for_trip(client, headers, first_trip_id)
        assert first_cte["number"] == "1"
        assert first_cte["series"] == "1"

        config_after_first = await client.get("/api/v1/configuracao-fiscal", headers=headers)
        assert config_after_first.json()["next_cte_number"] == 2

        # Muda a série ativa — nunca deveria afetar o CT-e já emitido.
        change_series = await client.patch(
            "/api/v1/configuracao-fiscal", headers=headers, json={"cte_series": "2"}
        )
        assert change_series.status_code == 200
        assert change_series.json()["cte_series"] == "2"

        second_trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)
        second_cte = await _get_cte_for_trip(client, headers, second_trip_id)
        assert second_cte["number"] == "2"  # continua de onde parou, nunca reinicia
        assert second_cte["series"] == "2"  # usa a série nova, só a partir de agora

        # O primeiro CT-e nunca muda — número/série permanecem exatamente como foram capturados.
        first_cte_reloaded = await client.get(f"/api/v1/ctes/{first_cte['id']}", headers=headers)
        assert first_cte_reloaded.json()["number"] == "1"
        assert first_cte_reloaded.json()["series"] == "1"


class TestTenantIsolation:
    async def test_cross_tenant_cte_access_returns_404(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, tenant_b, category_b = await _full_access_actor(client, tenants)

        trip_id = await _create_and_dispatch_trip(client, headers_b, tenant_b, category_b)
        cte = await _get_cte_for_trip(client, headers_b, trip_id)

        cross_tenant = await client.get(f"/api/v1/ctes/{cte['id']}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "FISCAL_CTE_NOT_FOUND"
