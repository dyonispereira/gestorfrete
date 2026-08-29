from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone

import httpx
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
from modules.freight.infrastructure.persistence.models.occurrence_model import OccurrenceModel
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
from modules.integration.application.job_internal_transitions import JobInternalTransitions
from modules.integration.application.webhook_internal_transitions import WebhookInternalTransitions
from modules.integration.domain.value_objects.job_result import JobResult
from modules.integration.infrastructure.persistence.models.integration_config_model import IntegrationConfigModel
from modules.integration.infrastructure.persistence.models.job_execution_model import JobExecutionModel
from modules.integration.infrastructure.persistence.models.webhook_model import WebhookModel
from modules.notification_center.infrastructure.persistence.models.channel_preference_model import (
    ChannelPreferenceModel,
)
from modules.notification_center.infrastructure.persistence.models.notification_model import NotificationModel
from modules.storage.infrastructure.persistence.models.file_model import FileModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel
from shared.collaboration.infrastructure.persistence.models.comment_model import CommentModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 10 — Recursos Transversais (D412-D417). D352 aplicado a Storage/File (MinIO
real), Attachment/Comment sobre Viagem, Busca Global, extensão da Timeline, Notificação, Integração/
Webhook/Job — mais as auditorias documentadas em cada um dos 4 sub-documentos de implementação."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.start", "Iniciar viagem", "freight"),
    ("freight.occurrence.create", "Criar ocorrências", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("storage.file.upload", "Enviar arquivo", "storage"),
    ("storage.file.view", "Ver metadados de arquivo", "storage"),
    ("storage.file.delete", "Excluir arquivo", "storage"),
    ("storage.attachment.view", "Ver anexo", "storage"),
    ("storage.attachment.create", "Criar anexo", "storage"),
    ("storage.attachment.delete", "Excluir anexo", "storage"),
    ("storage.comment.view", "Ver comentário", "storage"),
    ("storage.comment.create", "Criar comentário", "storage"),
    ("storage.comment.edit_own", "Editar o próprio comentário", "storage"),
    ("storage.comment.delete_own", "Excluir o próprio comentário", "storage"),
    ("notification_center.alert.view", "Ver notificações", "notification_center"),
    ("notification_center.alert.manage_own", "Marcar a própria notificação como lida", "notification_center"),
    ("notification_center.channel_preference.view", "Ver preferência de canal", "notification_center"),
    ("notification_center.channel_preference.edit", "Editar preferência de canal", "notification_center"),
    ("integration.config.view", "Ver configuração de integração", "integration"),
    ("integration.config.create", "Criar configuração de integração", "integration"),
    ("integration.config.edit", "Editar configuração de integração", "integration"),
    ("integration.config.enable", "Habilitar integração", "integration"),
    ("integration.config.disable", "Desabilitar integração", "integration"),
    ("integration.webhook.view", "Ver webhook", "integration"),
    ("integration.webhook.create", "Criar webhook", "integration"),
    ("integration.webhook.edit", "Editar webhook", "integration"),
    ("integration.webhook.activate", "Ativar webhook", "integration"),
    ("integration.webhook.suspend", "Suspender webhook", "integration"),
    ("integration.webhook.test", "Testar webhook", "integration"),
    ("integration.job.view", "Ver execução de job", "integration"),
    ("integration.job.trigger", "Disparar job", "integration"),
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


async def _create_user(
    tenant_id: uuid.UUID, *, role_ids: frozenset[uuid.UUID], driver_id: uuid.UUID | None = None
) -> tuple[uuid.UUID, str]:
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

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))

        # Lote 10 — filhos antes dos pais.
        await session.execute(delete(WebhookModel).where(WebhookModel.tenant_id == tenant_id))
        await session.execute(delete(IntegrationConfigModel).where(IntegrationConfigModel.tenant_id == tenant_id))
        await session.execute(delete(JobExecutionModel).where(JobExecutionModel.tenant_id == tenant_id))
        await session.execute(delete(NotificationModel).where(NotificationModel.tenant_id == tenant_id))
        await session.execute(delete(ChannelPreferenceModel).where(ChannelPreferenceModel.tenant_id == tenant_id))
        await session.execute(delete(AttachmentModel).where(AttachmentModel.tenant_id == tenant_id))
        await session.execute(delete(CommentModel).where(CommentModel.tenant_id == tenant_id))
        await session.execute(delete(FileModel).where(FileModel.tenant_id == tenant_id))

        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
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
    return str(resp.json()["id"])


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


async def _create_trip(client: AsyncClient, headers: dict[str, str], client_id: str) -> str:
    resp = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


async def _allocate_and_dispatch(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, trip_id: str, driver_id: str, vehicle_id: str,
) -> None:
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

    dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/start", headers=headers)
    assert dispatch.status_code == 200, dispatch.text


async def _upload_file(client: AsyncClient, headers: dict[str, str], content: bytes) -> tuple[str, str]:
    """Upload real via MinIO — devolve `(file_id, hash_sha256_esperado)`."""

    initiate = await client.post(
        "/api/v1/storage/uploads", headers=headers,
        json={"name": "evidencia.txt", "mime_type": "text/plain", "size_bytes": len(content), "origin": "UPLOAD_DIRETO"},
    )
    assert initiate.status_code == 201, initiate.text
    body = initiate.json()

    async with httpx.AsyncClient(timeout=10.0) as minio_client:
        put = await minio_client.put(body["upload_url"], content=content)
    assert put.status_code in (200, 204), put.text

    complete = await client.post(f"/api/v1/storage/uploads/{body['file_id']}/commands/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["hash"] == hashlib.sha256(content).hexdigest()

    return body["file_id"], complete.json()["hash"]


class TestStorageFlow:
    """D352 — upload real via MinIO, download-url round-trip, versionamento, exclusão."""

    async def test_upload_complete_download_delete(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        content = b"conteudo real de evidencia para o Lote 10"

        file_id, expected_hash = await _upload_file(client, headers, content)

        get_file = await client.get(f"/api/v1/storage/files/{file_id}", headers=headers)
        assert get_file.status_code == 200
        assert get_file.json()["hash"] == expected_hash
        assert get_file.json()["version"] == 1
        # `storage_key` nunca exposto (D314).
        assert "storage_key" not in get_file.json()

        download = await client.get(f"/api/v1/storage/files/{file_id}/download-url", headers=headers)
        assert download.status_code == 200
        async with httpx.AsyncClient(timeout=10.0) as minio_client:
            fetched = await minio_client.get(download.json()["download_url"])
        assert fetched.status_code == 200
        assert fetched.content == content

        # Nova versão — nunca sobrescreve (D324).
        new_content = b"conteudo real de evidencia, versao 2"
        initiate_v2 = await client.post(
            "/api/v1/storage/uploads", headers=headers,
            json={
                "name": "evidencia.txt", "mime_type": "text/plain", "size_bytes": len(new_content),
                "origin": "UPLOAD_DIRETO", "previous_file_id": file_id,
            },
        )
        assert initiate_v2.status_code == 201, initiate_v2.text
        async with httpx.AsyncClient(timeout=10.0) as minio_client:
            await minio_client.put(initiate_v2.json()["upload_url"], content=new_content)
        complete_v2 = await client.post(
            f"/api/v1/storage/uploads/{initiate_v2.json()['file_id']}/commands/complete", headers=headers
        )
        assert complete_v2.status_code == 200
        assert complete_v2.json()["version"] == 2

        versions = await client.get(f"/api/v1/storage/files/{file_id}/versions", headers=headers)
        assert versions.status_code == 200
        assert [v["version"] for v in versions.json()["data"]] == [2, 1]

        # Excluir a versão referenciada por um Anexo ativo é 409.
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)
        attach = await client.post(
            f"/api/v1/viagens/{trip_id}/attachments", headers=headers,
            json={"attachment_type": "FOTO", "file_id": file_id},
        )
        assert attach.status_code == 201, attach.text

        delete_in_use = await client.delete(f"/api/v1/storage/files/{file_id}", headers=headers)
        assert delete_in_use.status_code == 409
        assert delete_in_use.json()["error"]["code"] == "STORAGE_FILE_IN_USE"

        delete_v2 = await client.delete(f"/api/v1/storage/files/{initiate_v2.json()['file_id']}", headers=headers)
        assert delete_v2.status_code == 204


class TestAttachmentCommentAudits:
    """Auditorias documentadas em COLLABORATION_IMPLEMENTATION.md."""

    async def test_attachment_and_comment_full_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)
        file_id, _ = await _upload_file(client, headers, b"anexo de teste")

        # Nunca existe uma rota genérica POST /attachments — só sob o dono.
        create_attachment = await client.post(
            f"/api/v1/viagens/{trip_id}/attachments", headers=headers,
            json={"attachment_type": "FOTO", "file_id": file_id, "description": "Evidência"},
        )
        assert create_attachment.status_code == 201, create_attachment.text
        attachment_id = create_attachment.json()["id"]
        assert create_attachment.json()["audit"]["updated_at"] == create_attachment.json()["audit"]["created_at"]

        create_comment = await client.post(
            f"/api/v1/viagens/{trip_id}/comments", headers=headers, json={"text": "Primeiro comentário."}
        )
        assert create_comment.status_code == 201, create_comment.text
        comment_id = create_comment.json()["id"]

        # PATCH real — autor é o próprio ator.
        update_comment = await client.patch(
            f"/api/v1/viagens/{trip_id}/comments/{comment_id}", headers=headers, json={"text": "Editado."}
        )
        assert update_comment.status_code == 200
        assert update_comment.json()["text"] == "Editado."

        # Hard delete real — verificado diretamente no banco, não só via 404 num GET seguinte.
        delete_attachment = await client.delete(
            f"/api/v1/viagens/{trip_id}/attachments/{attachment_id}", headers=headers
        )
        assert delete_attachment.status_code == 204
        session_factory = get_session_factory()
        token = set_current_tenant_id(tenant_id)
        try:
            async with session_factory() as session:
                row = (
                    await session.execute(select(AttachmentModel).where(AttachmentModel.id == uuid.UUID(attachment_id)))
                ).scalar_one_or_none()
        finally:
            reset_current_tenant_id(token)
        assert row is None

        delete_comment = await client.delete(f"/api/v1/viagens/{trip_id}/comments/{comment_id}", headers=headers)
        assert delete_comment.status_code == 204

    async def test_edit_own_is_enforced_even_with_permission_granted(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers_a)
        trip_id = await _create_trip(client, headers_a, client_id)

        create_comment = await client.post(
            f"/api/v1/viagens/{trip_id}/comments", headers=headers_a, json={"text": "Comentário do usuário A."}
        )
        comment_id = create_comment.json()["id"]

        # Um segundo usuário do mesmo tenant, também com storage.comment.edit_own/delete_own.
        role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
        _, email_b = await _create_user(tenant_id, role_ids=frozenset({role_id}))
        headers_b = await _login(client, email_b)

        update_by_other = await client.patch(
            f"/api/v1/viagens/{trip_id}/comments/{comment_id}", headers=headers_b, json={"text": "Tentativa alheia."}
        )
        assert update_by_other.status_code == 403
        assert update_by_other.json()["error"]["code"] == "STORAGE_COMMENT_NOT_OWNED"

        delete_by_other = await client.delete(f"/api/v1/viagens/{trip_id}/comments/{comment_id}", headers=headers_b)
        assert delete_by_other.status_code == 403


class TestTimelineExtension:
    async def test_timeline_includes_attachments_and_comments(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)
        file_id, _ = await _upload_file(client, headers, b"anexo da timeline")

        await client.post(
            f"/api/v1/viagens/{trip_id}/attachments", headers=headers,
            json={"attachment_type": "FOTO", "file_id": file_id},
        )
        await client.post(f"/api/v1/viagens/{trip_id}/comments", headers=headers, json={"text": "Nota da timeline."})

        timeline = await client.get(f"/api/v1/viagens/{trip_id}/timeline", headers=headers)
        assert timeline.status_code == 200
        sources = {entry["source"] for entry in timeline.json()["data"]}
        assert "ANEXO" in sources
        assert "COMENTARIO" in sources


class TestGlobalSearchAudit:
    async def test_search_never_leaks_a_type_without_permission(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)
        trip_code = (await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)).json()["codigo"]

        full_search = await client.get("/api/v1/search", headers=headers, params={"q": trip_code})
        assert full_search.status_code == 200
        types_found = {g["entity_type"] for g in full_search.json()["results"]}
        assert "viagem" in types_found

        # Usuário sem freight.trip.view — o tipo "viagem" nunca aparece, mesmo achando o termo.
        role_id = await _create_role(tenant_id, ["crm.client.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
        limited_headers = await _login(client, email)

        limited_search = await client.get("/api/v1/search", headers=limited_headers, params={"q": trip_code})
        assert limited_search.status_code == 200
        limited_types = {g["entity_type"] for g in limited_search.json()["results"]}
        assert "viagem" not in limited_types


class TestNotificationAudits:
    async def test_dispatching_trip_notifies_allocated_driver_never_self(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        driver_id, _ = await _create_driver(client, headers)
        vehicle_id, _ = await _create_vehicle(client, headers, category_id)

        # O Motorista tem Usuário vinculado — recebe a notificação (ator != destinatário).
        driver_role_id = await _create_role(tenant_id, ["notification_center.alert.view", "notification_center.alert.manage_own"])
        driver_user_id, driver_email = await _create_user(
            tenant_id, role_ids=frozenset({driver_role_id}), driver_id=uuid.UUID(driver_id)
        )
        driver_headers = await _login(client, driver_email)

        trip_id = await _create_trip(client, headers, client_id)
        await _allocate_and_dispatch(client, headers, tenant_id, trip_id, driver_id, vehicle_id)

        driver_notifications = await client.get("/api/v1/notifications", headers=driver_headers)
        assert driver_notifications.status_code == 200
        assert driver_notifications.json()["meta"]["pagination"]["total"] == 1
        notification = driver_notifications.json()["data"][0]
        assert notification["origin_event_type"] == "ViagemDespachada"
        assert notification["status"] == "NAO_LIDA"

        # Gestor (ator do despacho) nunca recebe notificação da própria ação.
        gestor_notifications = await client.get("/api/v1/notifications", headers=headers)
        assert gestor_notifications.json()["meta"]["pagination"]["total"] == 0

        # Isolamento pessoal — Gestor não acessa a notificação do Motorista por ID (403, nunca 404).
        forbidden = await client.get(f"/api/v1/notifications/{notification['id']}", headers=headers)
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "NOTIFICATION_FORBIDDEN"

        # mark-read — segunda chamada é 409, nunca reprocessável silenciosamente.
        mark_read = await client.post(
            f"/api/v1/notifications/{notification['id']}/commands/mark-read", headers=driver_headers
        )
        assert mark_read.status_code == 200
        assert mark_read.json()["status"] == "LIDA"
        mark_read_again = await client.post(
            f"/api/v1/notifications/{notification['id']}/commands/mark-read", headers=driver_headers
        )
        assert mark_read_again.status_code == 409
        assert mark_read_again.json()["error"]["code"] == "NOTIFICATION_ALREADY_READ"

    async def test_disabled_channel_preference_blocks_notification_creation(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        driver_id, _ = await _create_driver(client, headers)
        vehicle_id, _ = await _create_vehicle(client, headers, category_id)

        driver_role_id = await _create_role(
            tenant_id,
            [
                "notification_center.alert.view", "notification_center.channel_preference.view",
                "notification_center.channel_preference.edit",
            ],
        )
        _, driver_email = await _create_user(
            tenant_id, role_ids=frozenset({driver_role_id}), driver_id=uuid.UUID(driver_id)
        )
        driver_headers = await _login(client, driver_email)

        # Três canais sempre presentes, default enabled=true sem preferência salva.
        preferences = await client.get("/api/v1/notifications/channel-preferences", headers=driver_headers)
        assert preferences.status_code == 200
        assert {p["channel"] for p in preferences.json()["data"]} == {"IN_APP", "PUSH", "EMAIL"}
        assert all(p["enabled"] for p in preferences.json()["data"])

        disable = await client.patch(
            "/api/v1/notifications/channel-preferences/IN_APP", headers=driver_headers, json={"enabled": False}
        )
        assert disable.status_code == 200
        assert disable.json()["enabled"] is False

        trip_id = await _create_trip(client, headers, client_id)
        await _allocate_and_dispatch(client, headers, tenant_id, trip_id, driver_id, vehicle_id)

        driver_notifications = await client.get("/api/v1/notifications", headers=driver_headers)
        assert driver_notifications.json()["meta"]["pagination"]["total"] == 0


class TestIntegrationConfigFlow:
    async def test_create_edit_enable_disable(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)
        file_id, _ = await _upload_file(client, headers, b"credencial-secreta-do-erp-externo")

        create = await client.post(
            "/api/v1/integrations", headers=headers, json={"type": "ERP Externo", "credential_file_id": file_id}
        )
        assert create.status_code == 201, create.text
        config_id = create.json()["id"]
        assert create.json()["status"] == "ATIVA"
        # Sem `audit` — DDL congelada não tem coluna de timestamp (D400-family).
        assert "audit" not in create.json()

        disable = await client.post(f"/api/v1/integrations/{config_id}/commands/disable", headers=headers)
        assert disable.status_code == 200
        assert disable.json()["status"] == "INATIVA"

        new_file_id, _ = await _upload_file(client, headers, b"nova-credencial-rotacionada")
        rotate = await client.patch(
            f"/api/v1/integrations/{config_id}", headers=headers, json={"credential_file_id": new_file_id}
        )
        assert rotate.status_code == 200
        assert rotate.json()["credential_file_id"] == new_file_id

        enable = await client.post(f"/api/v1/integrations/{config_id}/commands/enable", headers=headers)
        assert enable.status_code == 200
        assert enable.json()["status"] == "ATIVA"


class TestWebhookAudits:
    async def test_signing_secret_shown_once_and_three_failures_suspend(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/integrations/webhooks", headers=headers,
            json={
                "target_url": "https://example.invalid/webhook", "subscribed_events": ["ViagemDespachada"],
            },
        )
        assert create.status_code == 201, create.text
        webhook_id = create.json()["id"]
        assert create.json()["signing_secret"]
        assert create.json()["status"] == "ATIVO"

        get_after = await client.get(f"/api/v1/integrations/webhooks/{webhook_id}", headers=headers)
        assert get_after.status_code == 200
        assert get_after.json()["signing_secret"] is None

        token = set_current_tenant_id(tenant_id)
        try:
            simulator = WebhookInternalTransitions()
            await simulator.simulate_delivery_attempt(webhook_id=uuid.UUID(webhook_id), success=False)
            await simulator.simulate_delivery_attempt(webhook_id=uuid.UUID(webhook_id), success=False)
            still_active = await client.get(f"/api/v1/integrations/webhooks/{webhook_id}", headers=headers)
            assert still_active.json()["status"] == "ATIVO"
            await simulator.simulate_delivery_attempt(webhook_id=uuid.UUID(webhook_id), success=False)
        finally:
            reset_current_tenant_id(token)

        suspended = await client.get(f"/api/v1/integrations/webhooks/{webhook_id}", headers=headers)
        assert suspended.json()["status"] == "SUSPENSO"

        reactivate = await client.post(f"/api/v1/integrations/webhooks/{webhook_id}/commands/activate", headers=headers)
        assert reactivate.status_code == 200
        assert reactivate.json()["status"] == "ATIVO"


class TestJobAudits:
    async def test_unknown_job_type_is_rejected_and_valid_type_completes(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, _ = await _full_access_actor(client, tenants)

        unknown = await client.post(
            "/api/v1/jobs/commands/trigger", headers=headers, json={"job_type": "EXECUTAR_CODIGO_ARBITRARIO"}
        )
        assert unknown.status_code == 400
        assert unknown.json()["error"]["code"] == "JOB_TYPE_NOT_REGISTERED"

        trigger = await client.post(
            "/api/v1/jobs/commands/trigger", headers=headers, json={"job_type": "REPROCESSAMENTO_FILA_SINCRONIZACAO"}
        )
        assert trigger.status_code == 202, trigger.text
        job_id = trigger.json()["id"]
        assert trigger.json()["finished_at"] is None
        assert trigger.json()["result"] is None

        token = set_current_tenant_id(tenant_id)
        try:
            await JobInternalTransitions().complete_job(
                job_id=uuid.UUID(job_id), result=JobResult.SUCESSO, now=datetime.now(timezone.utc)
            )
        finally:
            reset_current_tenant_id(token)

        get_job = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert get_job.status_code == 200
        assert get_job.json()["result"] == "SUCESSO"

        listing = await client.get("/api/v1/jobs", headers=headers)
        assert listing.status_code == 200
        assert any(j["id"] == job_id for j in listing.json()["data"])

    async def test_trigger_requires_high_criticality_permission(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        _, tenant_id, _ = await _full_access_actor(client, tenants)
        role_id = await _create_role(tenant_id, ["integration.job.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
        limited_headers = await _login(client, email)

        trigger = await client.post(
            "/api/v1/jobs/commands/trigger", headers=limited_headers,
            json={"job_type": "REPROCESSAMENTO_FILA_SINCRONIZACAO"},
        )
        assert trigger.status_code == 403
