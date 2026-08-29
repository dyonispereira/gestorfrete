from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.ai.application.ai_inference_engine import AIInferenceEngine
from modules.ai.domain.value_objects.classification_type import ClassificationType
from modules.ai.domain.value_objects.inference_origin import InferenceOrigin
from modules.ai.domain.value_objects.reading_type import ReadingType
from modules.ai.infrastructure.persistence.models.ai_anomaly_model import AIAnomalyModel
from modules.ai.infrastructure.persistence.models.ai_classification_model import AIClassificationModel
from modules.ai.infrastructure.persistence.models.ai_feedback_model import AIFeedbackModel
from modules.ai.infrastructure.persistence.models.ai_inference_model import AIInferenceModel
from modules.ai.infrastructure.persistence.models.ai_model_model import AIModelModel
from modules.ai.infrastructure.persistence.models.ai_prediction_model import AIPredictionModel
from modules.ai.infrastructure.persistence.models.ai_suggestion_model import AISuggestionModel
from modules.ai.infrastructure.persistence.models.computer_vision_reading_model import ComputerVisionReadingModel
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
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
from modules.storage.infrastructure.persistence.models.file_model import FileModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 12 — IA (D161-D172, D309-D313, D423-D426). D352 aplicado às 8 entidades mais as
10 auditorias explícitas pedidas pelo usuário: (1) IA nunca altera domínio operacional diretamente;
(2) Modelo e versão congelados por Inferência; (3) confiança não vira decisão; (4) Visão
Computacional com revisão humana, reforçada em dois níveis; (5) evidência preservada
(`arquivo_origem_id` nunca substituído); (6) Feedback/resultado real sem alterar retroativamente a
saída original; (7) autorização por campo de custo (`ai.inference.view_cost`); (8) fornecedor
agnóstico — nenhum import de SDK real em `modules.ai`; (9) D426 — verificado manualmente via
`lint-imports` (ver ACHADOS em `docs/backend/ai/README.md`, mesmo precedente do Lote 1/11); (10)
nenhum Domain Event de IA inventado."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("crm.client.create", "Criar clientes", "crm"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.view", "Ver viagens", "freight"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("fleet.vehicle.view", "Ver veículos", "fleet"),
    ("storage.file.upload", "Enviar arquivo", "storage"),
    ("storage.file.view", "Ver metadados de arquivo", "storage"),
    ("ai.model.view", "Visualizar modelo de IA", "ai"),
    ("ai.model.create", "Criar modelo de IA", "ai"),
    ("ai.model.edit", "Editar modelo de IA", "ai"),
    ("ai.inference.view", "Visualizar inferência", "ai"),
    ("ai.inference.view_cost", "Visualizar custo da inferência", "ai"),
    ("ai.suggestion.view", "Visualizar sugestão de IA", "ai"),
    ("ai.suggestion.decide", "Aceitar/rejeitar/ignorar sugestão de IA", "ai"),
    ("ai.prediction.view", "Visualizar predição de IA", "ai"),
    ("ai.classification.view", "Visualizar classificação de IA", "ai"),
    ("ai.anomaly.view", "Visualizar anomalia detectada", "ai"),
    ("ai.anomaly.review", "Investigar/descartar anomalia detectada", "ai"),
    ("ai.computer_vision.view", "Visualizar leitura de visão computacional", "ai"),
    ("ai.computer_vision.confirm", "Confirmar/rejeitar leitura de visão computacional", "ai"),
    ("ai.feedback.view", "Visualizar feedback de IA", "ai"),
    ("ai.feedback.create", "Registrar feedback de IA", "ai"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]
VIEW_ONLY_NO_COST_CODES = [c for c in ALL_PERMISSION_CODES if c != "ai.inference.view_cost"]


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


async def _user_with_permissions(
    client: AsyncClient, tenant_id: uuid.UUID, permission_codes: list[str]
) -> dict[str, str]:
    role_id = await _create_role(tenant_id, permission_codes)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    return await _login(client, email)


async def _full_access_actor(client: AsyncClient, tenants: list[uuid.UUID]) -> tuple[dict[str, str], uuid.UUID]:
    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    headers = await _user_with_permissions(client, tenant_id, ALL_PERMISSION_CODES)
    return headers, tenant_id


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

        # Lote 12 (IA) — filhos antes dos pais; as 5 saídas de IA não têm FK física para
        # `inferencias_ia` (D202-style), então a ordem entre elas e `inferencias_ia` não importa por
        # integridade — mantida por clareza.
        await session.execute(delete(AIFeedbackModel).where(AIFeedbackModel.tenant_id == tenant_id))
        await session.execute(delete(ComputerVisionReadingModel).where(ComputerVisionReadingModel.tenant_id == tenant_id))
        await session.execute(delete(AIAnomalyModel).where(AIAnomalyModel.tenant_id == tenant_id))
        await session.execute(delete(AIClassificationModel).where(AIClassificationModel.tenant_id == tenant_id))
        await session.execute(delete(AIPredictionModel).where(AIPredictionModel.tenant_id == tenant_id))
        await session.execute(delete(AISuggestionModel).where(AISuggestionModel.tenant_id == tenant_id))
        await session.execute(delete(AIInferenceModel).where(AIInferenceModel.tenant_id == tenant_id))
        await session.execute(delete(AIModelModel).where(AIModelModel.tenant_id == tenant_id))

        await session.execute(delete(FileModel).where(FileModel.tenant_id == tenant_id))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleImpedimentModel).where(VehicleImpedimentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
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


async def _create_trip(client: AsyncClient, headers: dict[str, str], client_id: str) -> str:
    resp = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


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


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    plate = f"VG{uuid.uuid4().hex[:5].upper()}"
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": plate, "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Volvo", "modelo": "FH540",
            "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _get_trip_snapshot(client: AsyncClient, headers: dict[str, str], trip_id: str) -> dict:
    resp = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_ai_model(
    client: AsyncClient, headers: dict[str, str], *, name: str | None = None, logical_provider: str = "INTERNO",
    version: str = "1",
) -> dict:
    resp = await client.post(
        "/api/v1/ai/models", headers=headers,
        json={
            "name": name or f"Modelo {uuid.uuid4().hex[:8]}", "type": "CLASSIFICACAO", "version": version,
            "logical_provider": logical_provider,
            "capability": "Classifica risco de atraso a partir do histórico de rota e clima.",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _run_suggestion(
    tenant_id: uuid.UUID, *, model_id: uuid.UUID, entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID,
    input: dict | None = None,
):
    token = set_current_tenant_id(tenant_id)
    try:
        return await AIInferenceEngine().run_suggestion(
            model_id=model_id, input=input or {"seed": "sugestao"}, origem=InferenceOrigin.MANUAL,
            categoria="AlocacaoMotorista", entidade_alvo_tipo=entidade_alvo_tipo, entidade_alvo_id=entidade_alvo_id,
            recomendacao="Realocar o motorista X para esta Viagem.",
            justificativa="Motorista X está a 5km de distância, dentro da janela de coleta.",
            now=datetime.now(timezone.utc),
        )
    finally:
        reset_current_tenant_id(token)


async def _run_prediction(
    tenant_id: uuid.UUID, *, model_id: uuid.UUID, entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID,
    valid_until: datetime, input: dict | None = None,
):
    token = set_current_tenant_id(tenant_id)
    try:
        return await AIInferenceEngine().run_prediction(
            model_id=model_id, input=input or {"seed": "predicao"}, origem=InferenceOrigin.MANUAL,
            categoria="ManutencaoPreventiva", entidade_alvo_tipo=entidade_alvo_tipo,
            entidade_alvo_id=entidade_alvo_id, valor_previsto=Decimal("72.50"),
            data_hora_validade_fim=valid_until, now=datetime.now(timezone.utc),
        )
    finally:
        reset_current_tenant_id(token)


async def _run_classification(
    tenant_id: uuid.UUID, *, model_id: uuid.UUID, entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID,
    input: dict | None = None,
):
    token = set_current_tenant_id(tenant_id)
    try:
        return await AIInferenceEngine().run_classification(
            model_id=model_id, input=input or {"seed": "classificacao"}, origem=InferenceOrigin.MANUAL,
            tipo_classificacao=ClassificationType.RISCO, entidade_alvo_tipo=entidade_alvo_tipo,
            entidade_alvo_id=entidade_alvo_id, rotulo="Alto", now=datetime.now(timezone.utc),
        )
    finally:
        reset_current_tenant_id(token)


async def _run_anomaly(
    tenant_id: uuid.UUID, *, model_id: uuid.UUID, leitura_origem_tipo: str, leitura_origem_id: uuid.UUID,
    input: dict | None = None,
):
    token = set_current_tenant_id(tenant_id)
    try:
        return await AIInferenceEngine().run_anomaly_detection(
            model_id=model_id, input=input or {"seed": "anomalia"}, origem=InferenceOrigin.AUTOMATICO,
            leitura_origem_tipo=leitura_origem_tipo, leitura_origem_id=leitura_origem_id,
            now=datetime.now(timezone.utc),
        )
    finally:
        reset_current_tenant_id(token)


async def _run_computer_vision_below_threshold(tenant_id: uuid.UUID, *, model_id: uuid.UUID, arquivo_origem_id: uuid.UUID):
    """Tenta várias entradas até achar uma cujo hash determinístico produza confiança < 80 (limiar
    fixo de `AIInferenceEngine`, D424) — necessário para `revisao_humana_necessaria=True`."""

    token = set_current_tenant_id(tenant_id)
    try:
        engine = AIInferenceEngine()
        for seed in range(60):
            reading = await engine.run_computer_vision(
                model_id=model_id, input={"seed": seed}, origem=InferenceOrigin.AUTOMATICO,
                arquivo_origem_id=arquivo_origem_id, tipo_leitura=ReadingType.CANHOTO, regiao_analisada=None,
                now=datetime.now(timezone.utc),
            )
            if reading.revisao_humana_necessaria:
                return reading
        raise AssertionError("Nenhuma seed produziu confiança abaixo do limiar em 60 tentativas.")
    finally:
        reset_current_tenant_id(token)


async def _upload_file(client: AsyncClient, headers: dict[str, str], content: bytes) -> str:
    initiate = await client.post(
        "/api/v1/storage/uploads", headers=headers,
        json={"name": "canhoto.jpg", "mime_type": "image/jpeg", "size_bytes": len(content), "origin": "UPLOAD_DIRETO"},
    )
    assert initiate.status_code == 201, initiate.text
    body = initiate.json()

    async with httpx.AsyncClient(timeout=10.0) as minio_client:
        put = await minio_client.put(body["upload_url"], content=content)
    assert put.status_code in (200, 204), put.text

    complete = await client.post(f"/api/v1/storage/uploads/{body['file_id']}/commands/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["hash"] == hashlib.sha256(content).hexdigest()
    return body["file_id"]


# --------------------------------------------------------------------------------------
# Auditoria 1 + 3 — IA nunca altera domínio operacional diretamente; confiança não vira decisão.
# --------------------------------------------------------------------------------------


class TestSuggestionNeverAltersOperationalDomain:
    async def test_creating_and_accepting_suggestion_never_touches_trip_or_vehicle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)

        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)
        category_id = await _seed_vehicle_category(tenant_id)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        trip_before = await _get_trip_snapshot(client, headers, trip_id)
        vehicle_resp_before = await client.get(f"/api/v1/veiculos/{vehicle_id}", headers=headers)
        assert vehicle_resp_before.status_code == 200
        vehicle_before = vehicle_resp_before.json()

        suggestion = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        # Auditoria 3 — mesmo uma Inferência de alta confiança não decide sozinha.
        assert suggestion.nivel_confianca >= Decimal("0")

        trip_after_suggestion = await _get_trip_snapshot(client, headers, trip_id)
        assert trip_after_suggestion == trip_before

        # Aceitar a sugestão (decisão humana explícita) — D311: só registra a decisão, nunca
        # executa o comando operacional por conta própria.
        accept = await client.post(
            f"/api/v1/ai/suggestions/{suggestion.id}/commands/accept", headers=headers
        )
        assert accept.status_code == 200, accept.text
        assert accept.json()["status"] == "ACEITA"
        assert accept.json()["decision_user_id"] is not None

        trip_after_accept = await _get_trip_snapshot(client, headers, trip_id)
        vehicle_resp_after = await client.get(f"/api/v1/veiculos/{vehicle_id}", headers=headers)
        assert vehicle_resp_after.status_code == 200

        # Auditoria 1 — Viagem e Frota permanecem byte-a-byte inalterados sem um comando explícito
        # do bounded context proprietário.
        assert trip_after_accept == trip_before
        assert vehicle_resp_after.json() == vehicle_before

        # Reaceitar (ou rejeitar/ignorar) uma Sugestão já decidida é sempre recusado.
        accept_again = await client.post(
            f"/api/v1/ai/suggestions/{suggestion.id}/commands/accept", headers=headers
        )
        assert accept_again.status_code == 409
        assert accept_again.json()["error"]["code"] == "AI_SUGGESTION_INVALID_TRANSITION"

    async def test_reject_and_ignore_transitions(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)

        suggestion_a = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        reject = await client.post(
            f"/api/v1/ai/suggestions/{suggestion_a.id}/commands/reject", headers=headers,
            json={"justification": "Motorista já alocado em outra rota."},
        )
        assert reject.status_code == 200
        assert reject.json()["status"] == "REJEITADA"

        suggestion_b = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        ignore = await client.post(f"/api/v1/ai/suggestions/{suggestion_b.id}/commands/ignore", headers=headers)
        assert ignore.status_code == 200
        assert ignore.json()["status"] == "IGNORADA"


# --------------------------------------------------------------------------------------
# Auditoria 2 — Modelo e versão congelados por Inferência.
# --------------------------------------------------------------------------------------


class TestModelVersionFrozenPerInference:
    async def test_new_model_version_and_discontinuation_never_change_existing_inference(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model_name = f"Classificador de Risco {uuid.uuid4().hex[:6]}"
        model_v1 = await _create_ai_model(client, headers, name=model_name, version="1")

        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)

        suggestion = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model_v1["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        get_inference = await client.get(f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=headers)
        assert get_inference.status_code == 200
        assert get_inference.json()["model_id"] == model_v1["id"]
        assert get_inference.json()["model_version"] == "1"

        # D169 — múltiplos Modelos coexistem; "nova versão" é sempre uma linha física nova.
        model_v2 = await _create_ai_model(client, headers, name=model_name, version="2")
        assert model_v2["id"] != model_v1["id"]

        # "Aposentar" a v1 (não existe conceito de versão ativa única, D169) não altera a Inferência
        # já executada.
        discontinue = await client.patch(
            f"/api/v1/ai/models/{model_v1['id']}", headers=headers, json={"status": "DESCONTINUADO"}
        )
        assert discontinue.status_code == 200
        assert discontinue.json()["status"] == "DESCONTINUADO"

        get_inference_again = await client.get(
            f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=headers
        )
        assert get_inference_again.status_code == 200
        assert get_inference_again.json()["model_id"] == model_v1["id"]
        assert get_inference_again.json()["model_version"] == "1"

        get_suggestion_again = await client.get(f"/api/v1/ai/suggestions/{suggestion.id}", headers=headers)
        assert get_suggestion_again.status_code == 200
        assert get_suggestion_again.json()["inference_id"] == str(suggestion.inferencia_ia_id)

        # `PATCH` nunca edita a identidade do modelo (nome/tipo/versão/fornecedor).
        attempt_edit_identity = await client.patch(
            f"/api/v1/ai/models/{model_v1['id']}", headers=headers, json={"capability": "Nova descrição funcional."}
        )
        assert attempt_edit_identity.status_code == 200
        assert attempt_edit_identity.json()["version"] == "1"
        assert attempt_edit_identity.json()["name"] == model_name

    async def test_duplicate_name_and_version_conflicts(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)
        model_name = f"Modelo Duplicado {uuid.uuid4().hex[:6]}"
        await _create_ai_model(client, headers, name=model_name, version="1")

        duplicate = await client.post(
            "/api/v1/ai/models", headers=headers,
            json={
                "name": model_name, "type": "CLASSIFICACAO", "version": "1", "logical_provider": "INTERNO",
                "capability": "Duplicata proposital.",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "AI_MODEL_NAME_VERSION_ALREADY_EXISTS"


# --------------------------------------------------------------------------------------
# Auditoria 4 — Visão Computacional com revisão humana, reforçada em dois níveis.
# --------------------------------------------------------------------------------------


class TestComputerVisionHumanReview:
    async def test_confirmation_required_and_enforced_at_application_and_database_level(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        file_id = await _upload_file(client, headers, b"conteudo simulado de canhoto fotografado")

        reading = await _run_computer_vision_below_threshold(
            tenant_id, model_id=uuid.UUID(model["id"]), arquivo_origem_id=uuid.UUID(file_id)
        )
        assert reading.revisao_humana_necessaria is True
        assert reading.usuario_confirmacao_id is None

        get_before = await client.get(f"/api/v1/ai/computer-vision/readings/{reading.id}", headers=headers)
        assert get_before.status_code == 200
        assert get_before.json()["status"] == "PROCESSADA"
        assert get_before.json()["human_review_required"] is True

        confirm = await client.post(
            f"/api/v1/ai/computer-vision/readings/{reading.id}/commands/confirm", headers=headers
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["status"] == "CONFIRMADA"
        assert confirm.json()["confirmation_user_id"] is not None

        # Confirmar de novo (já não está mais PROCESSADA) é recusado pela Application.
        confirm_again = await client.post(
            f"/api/v1/ai/computer-vision/readings/{reading.id}/commands/confirm", headers=headers
        )
        assert confirm_again.status_code == 409
        assert confirm_again.json()["error"]["code"] == "AI_CV_READING_INVALID_TRANSITION"

        # Auditoria 4, segunda camada — a constraint física do Postgres bloqueia mesmo contornando
        # a Application: tenta gravar CONFIRMADA/revisão-necessária sem usuario_confirmacao_id via
        # SQL direto (outra leitura, para não corromper o registro já testado acima).
        second_reading = await _run_computer_vision_below_threshold(
            tenant_id, model_id=uuid.UUID(model["id"]), arquivo_origem_id=uuid.UUID(file_id)
        )
        session_factory = get_session_factory()
        async with session_factory() as session:
            with pytest.raises(IntegrityError, match="ck_leituras_visao_computacional_confirmacao_humana"):
                await session.execute(
                    update(ComputerVisionReadingModel)
                    .where(ComputerVisionReadingModel.id == second_reading.id)
                    .values(status="CONFIRMADA", usuario_confirmacao_id=None)
                )
                await session.flush()
            await session.rollback()

        # O registro contornado nunca foi persistido — continua PROCESSADA.
        get_second = await client.get(
            f"/api/v1/ai/computer-vision/readings/{second_reading.id}", headers=headers
        )
        assert get_second.status_code == 200
        assert get_second.json()["status"] == "PROCESSADA"


# --------------------------------------------------------------------------------------
# Auditoria 5 — evidência preservada (`arquivo_origem_id` nunca substituído por binário).
# --------------------------------------------------------------------------------------


class TestEvidencePreserved:
    async def test_source_file_never_replaced_by_binary_and_stays_unchanged(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        content = b"foto real de canhoto para evidencia"
        file_id = await _upload_file(client, headers, content)

        file_before = await client.get(f"/api/v1/storage/files/{file_id}", headers=headers)
        assert file_before.status_code == 200

        reading = await _run_computer_vision_below_threshold(
            tenant_id, model_id=uuid.UUID(model["id"]), arquivo_origem_id=uuid.UUID(file_id)
        )
        get_reading = await client.get(f"/api/v1/ai/computer-vision/readings/{reading.id}", headers=headers)
        assert get_reading.status_code == 200
        body = get_reading.json()

        # `source_file_id` é sempre a referência ao Arquivo — nunca binário/base64 embutido.
        assert body["source_file_id"] == file_id
        assert isinstance(body["extracted_result"], dict)
        assert "base64" not in str(body["extracted_result"]).lower()

        await client.post(f"/api/v1/ai/computer-vision/readings/{reading.id}/commands/confirm", headers=headers)

        # O Arquivo original nunca é tocado pelo processamento/confirmação da Leitura.
        file_after = await client.get(f"/api/v1/storage/files/{file_id}", headers=headers)
        assert file_after.status_code == 200
        assert file_after.json() == file_before.json()


# --------------------------------------------------------------------------------------
# Auditoria 6 — Feedback e resultado real sem alterar retroativamente a saída original.
# --------------------------------------------------------------------------------------


class TestFeedbackNeverAltersOriginal:
    async def test_feedback_and_actual_result_never_retroactively_change_suggestion_or_inference(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)

        suggestion = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        inference_before = await client.get(
            f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=headers
        )
        assert inference_before.status_code == 200

        create_feedback = await client.post(
            "/api/v1/ai/feedback", headers=headers,
            json={
                "output_type": "SUGESTAO", "output_id": str(suggestion.id), "result": "ACEITO",
                "justification": "Recomendação fez sentido operacionalmente.",
            },
        )
        assert create_feedback.status_code == 201, create_feedback.text
        feedback_id = create_feedback.json()["id"]
        assert create_feedback.json()["actual_result"] is None

        # Registrar Feedback NÃO altera a Sugestão (que continua PENDENTE — feedback é observação
        # independente, nunca a decisão em si) nem a Inferência original.
        suggestion_after_feedback = await client.get(f"/api/v1/ai/suggestions/{suggestion.id}", headers=headers)
        assert suggestion_after_feedback.status_code == 200
        assert suggestion_after_feedback.json()["status"] == "PENDENTE"

        inference_after_feedback = await client.get(
            f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=headers
        )
        assert inference_after_feedback.json() == inference_before.json()

        # D192 — resultado real registrado depois, via PATCH, sem alterar `result`/`justification`.
        update_feedback = await client.patch(
            f"/api/v1/ai/feedback/{feedback_id}", headers=headers,
            json={"actual_result": "Motorista chegou 10 minutos adiantado."},
        )
        assert update_feedback.status_code == 200, update_feedback.text
        assert update_feedback.json()["actual_result"] == "Motorista chegou 10 minutos adiantado."
        assert update_feedback.json()["result"] == "ACEITO"
        assert update_feedback.json()["justification"] == "Recomendação fez sentido operacionalmente."

        # Feedback referenciando uma saída inexistente é 404, nunca criado silenciosamente.
        missing_output = await client.post(
            "/api/v1/ai/feedback", headers=headers,
            json={"output_type": "SUGESTAO", "output_id": str(uuid.uuid4()), "result": "REJEITADO"},
        )
        assert missing_output.status_code == 404
        assert missing_output.json()["error"]["code"] == "AI_SUGGESTION_NOT_FOUND"


# --------------------------------------------------------------------------------------
# Auditoria 7 — autorização por campo de custo (`ai.inference.view_cost`).
# --------------------------------------------------------------------------------------


class TestInferenceCostAuthorization:
    async def test_cost_visible_only_with_view_cost_permission(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        # Fornecedor externo — FakeAIModelGateway só preenche `cost` para PROVEDOR_EXTERNO.
        model = await _create_ai_model(client, headers, logical_provider="PROVEDOR_EXTERNO")
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)

        suggestion = await _run_suggestion(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )

        full_access = await client.get(
            f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=headers
        )
        assert full_access.status_code == 200
        assert full_access.json()["cost"] is not None

        no_cost_headers = await _user_with_permissions(client, tenant_id, VIEW_ONLY_NO_COST_CODES)
        limited_access = await client.get(
            f"/api/v1/ai/inferences/{suggestion.inferencia_ia_id}", headers=no_cost_headers
        )
        assert limited_access.status_code == 200
        assert limited_access.json()["cost"] is None
        # Os demais campos continuam visíveis — `ai.inference.view_cost` só mascara `cost`.
        assert limited_access.json()["model_id"] == model["id"]
        assert limited_access.json()["status"] == "SUCESSO"

        # Mesma auditoria na listagem cursor-paginada.
        list_no_cost = await client.get("/api/v1/ai/inferences", headers=no_cost_headers)
        assert list_no_cost.status_code == 200
        assert all(item["cost"] is None for item in list_no_cost.json()["data"])


# --------------------------------------------------------------------------------------
# Auditoria 8 — D170, fornecedor agnóstico: nenhum import de SDK real em `modules.ai`.
# --------------------------------------------------------------------------------------


class TestProviderAgnostic:
    def test_no_real_provider_sdk_imported_anywhere_in_ai_module(self) -> None:
        """D170/D309 — os nomes de provedores reais aparecem propositalmente em docstrings/
        comentários (explicando o que NUNCA deve ser importado) — a auditoria precisa checar
        `import`/`from` de verdade via AST, nunca um grep textual ingênuo que confundiria prosa
        explicativa com uso real."""

        import ast

        forbidden_roots = {
            "openai", "anthropic", "google", "vertexai", "azure", "boto3", "botocore", "cohere",
            "ollama", "huggingface_hub", "transformers", "replicate",
        }
        ai_module_root = Path(__file__).resolve().parents[2] / "src" / "modules" / "ai"
        assert ai_module_root.is_dir(), f"Diretório do módulo ai não encontrado: {ai_module_root}"

        offending: list[str] = []
        for path in ai_module_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        if root in forbidden_roots:
                            offending.append(f"{path}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    if root in forbidden_roots:
                        offending.append(f"{path}: from {node.module} import ...")

        assert offending == [], f"SDK de provedor real encontrado em modules.ai: {offending}"


# --------------------------------------------------------------------------------------
# Auditoria 10 — nenhum Domain Event de IA inventado.
# --------------------------------------------------------------------------------------


class TestNoInventedDomainEvents:
    def test_ai_domain_events_directory_stays_empty(self) -> None:
        events_dir = Path(__file__).resolve().parents[2] / "src" / "modules" / "ai" / "domain" / "events"
        assert events_dir.is_dir()
        python_files = [p.name for p in events_dir.glob("*.py") if p.name != "__init__.py"]
        assert python_files == [], (
            f"Domain Event(s) de IA inventado(s) sem aprovação em EVENT_MAP.md: {python_files}"
        )


# --------------------------------------------------------------------------------------
# D352 — ciclo de vida completo: Predição/Classificação (D425 status recalculado), Anomalia
# (única transição real), tenant isolation de Modelo de IA.
# --------------------------------------------------------------------------------------


class TestPredictionClassificationAnomalyAndTenantIsolation:
    async def test_prediction_status_recomputed_at_read_time(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        category_id = await _seed_vehicle_category(tenant_id)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        now = datetime.now(timezone.utc)
        current_prediction = await _run_prediction(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VEICULO_TRACIONADOR",
            entidade_alvo_id=uuid.UUID(vehicle_id), valid_until=now + timedelta(days=3),
        )
        expired_prediction = await _run_prediction(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VEICULO_TRACIONADOR",
            entidade_alvo_id=uuid.UUID(vehicle_id), valid_until=now - timedelta(hours=1),
        )

        get_current = await client.get(f"/api/v1/ai/predictions/{current_prediction.id}", headers=headers)
        assert get_current.status_code == 200
        assert get_current.json()["status"] == "ATUAL"

        # D312/D425 — a coluna física gravada é sempre ATUAL (sem job de expiração nesta fundação),
        # mas a leitura recalcula o status EFETIVO sempre.
        get_expired = await client.get(f"/api/v1/ai/predictions/{expired_prediction.id}", headers=headers)
        assert get_expired.status_code == 200
        assert get_expired.json()["status"] == "EXPIRADA"

        list_default = await client.get("/api/v1/ai/predictions", headers=headers)
        assert list_default.status_code == 200
        listed_ids = {item["id"] for item in list_default.json()["data"]}
        assert str(current_prediction.id) in listed_ids
        assert str(expired_prediction.id) not in listed_ids

        list_include_expired = await client.get(
            "/api/v1/ai/predictions", headers=headers, params={"include_expired": "true"}
        )
        assert list_include_expired.status_code == 200
        listed_ids_all = {item["id"] for item in list_include_expired.json()["data"]}
        assert str(expired_prediction.id) in listed_ids_all

    async def test_classification_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)
        client_id = await _create_client_entity(client, headers)
        trip_id = await _create_trip(client, headers, client_id)

        classification = await _run_classification(
            tenant_id, model_id=uuid.UUID(model["id"]), entidade_alvo_tipo="VIAGEM",
            entidade_alvo_id=uuid.UUID(trip_id),
        )
        get_classification = await client.get(
            f"/api/v1/ai/classifications/{classification.id}", headers=headers
        )
        assert get_classification.status_code == 200
        body = get_classification.json()
        assert body["classification_type"] == "RISCO"
        assert body["label"] == "Alto"
        assert body["target_entity_id"] == trip_id

        list_by_target = await client.get(
            "/api/v1/ai/classifications", headers=headers,
            params={"target_entity_type": "VIAGEM", "target_entity_id": trip_id},
        )
        assert list_by_target.status_code == 200
        assert any(item["id"] == str(classification.id) for item in list_by_target.json()["data"])

    async def test_anomaly_review_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        model = await _create_ai_model(client, headers)

        anomaly = await _run_anomaly(
            tenant_id, model_id=uuid.UUID(model["id"]), leitura_origem_tipo="LEITURA_TELEMETRIA",
            leitura_origem_id=uuid.uuid4(),
        )
        get_before = await client.get(f"/api/v1/ai/anomalies/{anomaly.id}", headers=headers)
        assert get_before.status_code == 200
        assert get_before.json()["status"] == "ABERTA"

        review = await client.post(
            f"/api/v1/ai/anomalies/{anomaly.id}/commands/review", headers=headers,
            json={"resolution": "INVESTIGADA", "notes": "Correlacionado com pico de temperatura ambiente."},
        )
        assert review.status_code == 200, review.text
        assert review.json()["status"] == "INVESTIGADA"

        review_again = await client.post(
            f"/api/v1/ai/anomalies/{anomaly.id}/commands/review", headers=headers,
            json={"resolution": "DESCARTADA"},
        )
        assert review_again.status_code == 409
        assert review_again.json()["error"]["code"] == "AI_ANOMALY_INVALID_TRANSITION"

    async def test_ai_model_tenant_isolation(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _ = await _full_access_actor(client, tenants)
        headers_b, _ = await _full_access_actor(client, tenants)

        model_a = await _create_ai_model(client, headers_a, name=f"Modelo Privado A {uuid.uuid4().hex[:6]}")

        cross_tenant_get = await client.get(f"/api/v1/ai/models/{model_a['id']}", headers=headers_b)
        assert cross_tenant_get.status_code == 404

        list_b = await client.get("/api/v1/ai/models", headers=headers_b)
        assert list_b.status_code == 200
        assert all(item["id"] != model_a["id"] for item in list_b.json()["data"])
