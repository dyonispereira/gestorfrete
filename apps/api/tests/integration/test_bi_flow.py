from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.exceptions.base import ConflictError
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.analytics.application.analytics_calculation_engine import AnalyticsCalculationEngine
from modules.analytics.infrastructure.persistence.models.analytical_snapshot_model import (
    AnalyticalSnapshotIndicatorModel,
    AnalyticalSnapshotModel,
)
from modules.analytics.infrastructure.persistence.models.analytics_cube_model import (
    AnalyticsCubeMetricModel,
    AnalyticsCubeModel,
)
from modules.analytics.infrastructure.persistence.models.consolidated_indicator_model import (
    ConsolidatedIndicatorModel,
)
from modules.analytics.infrastructure.persistence.models.metric_model import MetricModel
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
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
from modules.reporting.application.reporting_internal_transitions import ReportingInternalTransitions
from modules.reporting.infrastructure.persistence.models.dashboard_model import DashboardModel
from modules.reporting.infrastructure.persistence.models.export_model import ExportModel
from modules.reporting.infrastructure.persistence.models.saved_filter_model import SavedFilterModel
from modules.reporting.infrastructure.persistence.models.saved_report_model import (
    SavedReportMetricModel,
    SavedReportModel,
)
from modules.reporting.infrastructure.persistence.models.scheduled_update_model import ScheduledUpdateModel
from modules.storage.infrastructure.persistence.models.file_model import FileModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 11 — BI (D090/D149/D418-D422). D352 aplicado a `analytics`/`reporting`, mais as
8 auditorias explícitas pedidas pelo usuário: (1) versão de Métrica respeitada pelo Indicador já
calculado; (2) `ConsolidatedIndicatorResponse` nunca inclui `formula`; (3) Snapshot imutável depois
de CONSOLIDADO — recalcular um Indicador já SNAPSHOTADO é `ConflictError`; (4) correção posterior de
`receita_realizada` de uma Viagem não altera um Indicador já SNAPSHOTADO; (5) Dashboard nunca
armazena valor numérico, só configuração; (6) isolamento por tenant + Platform Reference Data
(D046); (7) Exportação com erro rastreável (`ReportingInternalTransitions.fail_export`); (8) D421 —
verificado manualmente via `lint-imports` (ver ACHADOS em `docs/backend/bi/README.md`, mesmo
precedente do Lote 1/DEPENDENCY_RULES.md: prova pontual de que o gate barra uma violação
deliberada, não um teste permanente)."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("crm.client.create", "Criar clientes", "crm"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("storage.file.upload", "Enviar arquivo", "storage"),
    ("storage.file.view", "Ver metadados de arquivo", "storage"),
    ("analytics.metric.view", "Visualizar métrica", "analytics"),
    ("analytics.metric.create", "Criar métrica", "analytics"),
    ("analytics.metric.edit", "Editar métrica", "analytics"),
    ("analytics.indicator.view", "Visualizar indicador consolidado", "analytics"),
    ("analytics.snapshot.view", "Visualizar snapshot analítico", "analytics"),
    ("analytics.snapshot.create", "Iniciar consolidação de snapshot", "analytics"),
    ("analytics.cube.view", "Visualizar cubo analítico", "analytics"),
    ("analytics.cube.create", "Criar cubo analítico", "analytics"),
    ("analytics.cube.edit", "Editar cubo analítico", "analytics"),
    ("reporting.dashboard.view_own", "Visualizar os próprios dashboards", "reporting"),
    ("reporting.dashboard.view_shared", "Visualizar dashboards compartilhados", "reporting"),
    ("reporting.dashboard.create", "Criar dashboard", "reporting"),
    ("reporting.dashboard.edit_own", "Editar o próprio dashboard", "reporting"),
    ("reporting.dashboard.delete_own", "Excluir o próprio dashboard", "reporting"),
    ("reporting.dashboard.share", "Compartilhar dashboard", "reporting"),
    ("reporting.saved_filter.view_own", "Visualizar os próprios filtros salvos", "reporting"),
    ("reporting.saved_filter.create", "Criar filtro salvo", "reporting"),
    ("reporting.saved_filter.edit_own", "Editar o próprio filtro salvo", "reporting"),
    ("reporting.saved_filter.delete_own", "Excluir o próprio filtro salvo", "reporting"),
    ("reporting.saved_report.view_own", "Visualizar os próprios relatórios salvos", "reporting"),
    ("reporting.saved_report.create", "Criar relatório salvo", "reporting"),
    ("reporting.saved_report.edit_own", "Editar o próprio relatório salvo", "reporting"),
    ("reporting.saved_report.delete_own", "Excluir o próprio relatório salvo", "reporting"),
    ("reporting.export.view_own", "Visualizar as próprias exportações", "reporting"),
    ("reporting.export.create", "Solicitar exportação", "reporting"),
    ("reporting.scheduled_update.view", "Visualizar agendamento de atualização", "reporting"),
    ("reporting.scheduled_update.create", "Criar agendamento de atualização", "reporting"),
    ("reporting.scheduled_update.edit", "Editar agendamento de atualização", "reporting"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]
VIEW_OWN_ONLY_CODES = [c for c, _, _ in PERMISSION_CATALOG if c != "reporting.dashboard.view_shared"]
VIEW_SHARED_CODES = ["reporting.dashboard.view_own", "reporting.dashboard.view_shared"]


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

        # Lote 11 (BI) — filhos antes dos pais; tabelas de junção não têm `tenant_id` (D090/D149
        # nunca introduziram essa coluna nelas), sempre via subquery do pai.
        snapshot_ids = select(AnalyticalSnapshotModel.id).where(AnalyticalSnapshotModel.tenant_id == tenant_id)
        cube_ids = select(AnalyticsCubeModel.id).where(AnalyticsCubeModel.tenant_id == tenant_id)
        report_ids = select(SavedReportModel.id).where(SavedReportModel.tenant_id == tenant_id)

        await session.execute(
            delete(AnalyticalSnapshotIndicatorModel).where(
                AnalyticalSnapshotIndicatorModel.snapshot_analitico_id.in_(snapshot_ids)
            )
        )
        await session.execute(
            delete(AnalyticsCubeMetricModel).where(AnalyticsCubeMetricModel.cubo_analitico_id.in_(cube_ids))
        )
        await session.execute(
            delete(SavedReportMetricModel).where(SavedReportMetricModel.relatorio_salvo_id.in_(report_ids))
        )
        await session.execute(delete(ExportModel).where(ExportModel.tenant_id == tenant_id))
        await session.execute(delete(ScheduledUpdateModel).where(ScheduledUpdateModel.tenant_id == tenant_id))
        await session.execute(delete(ConsolidatedIndicatorModel).where(ConsolidatedIndicatorModel.tenant_id == tenant_id))
        await session.execute(delete(AnalyticalSnapshotModel).where(AnalyticalSnapshotModel.tenant_id == tenant_id))
        await session.execute(delete(SavedReportModel).where(SavedReportModel.tenant_id == tenant_id))
        await session.execute(delete(DashboardModel).where(DashboardModel.tenant_id == tenant_id))
        await session.execute(delete(SavedFilterModel).where(SavedFilterModel.tenant_id == tenant_id))
        await session.execute(delete(AnalyticsCubeModel).where(AnalyticsCubeModel.tenant_id == tenant_id))
        await session.execute(delete(MetricModel).where(MetricModel.tenant_id == tenant_id))
        await session.execute(delete(FileModel).where(FileModel.tenant_id == tenant_id))

        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
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


async def _create_trip_with_revenue(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, *, value: Decimal
) -> str:
    client_id = await _create_client_entity(client, headers)
    trip_id = await _create_trip(client, headers, client_id)
    token = set_current_tenant_id(tenant_id)
    try:
        await TripInternalTransitions().update_realized_revenue(trip_id=uuid.UUID(trip_id), value=value)
    finally:
        reset_current_tenant_id(token)
    return trip_id


async def _correct_trip_revenue(tenant_id: uuid.UUID, trip_id: str, *, value: Decimal) -> None:
    token = set_current_tenant_id(tenant_id)
    try:
        await TripInternalTransitions().update_realized_revenue(trip_id=uuid.UUID(trip_id), value=value)
    finally:
        reset_current_tenant_id(token)


async def _create_metric(
    client: AsyncClient, headers: dict[str, str], *, name: str | None = None, formula: str = "SUM(receita_realizada)",
) -> dict:
    resp = await client.post(
        "/api/v1/analytics/metrics", headers=headers,
        json={
            "name": name or f"Receita de Viagem {uuid.uuid4().hex[:8]}", "formula": formula,
            "temporal_granularity": "DIARIO", "dimensional_granularity": "VIAGEM", "unit": "BRL",
            "calculation_periodicity": "MANUAL",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _calculate_indicator(
    tenant_id: uuid.UUID, *, metric_id: uuid.UUID, trip_id: uuid.UUID, now: datetime,
):
    token = set_current_tenant_id(tenant_id)
    try:
        return await AnalyticsCalculationEngine().calculate_trip_revenue_indicator(
            metric_id=metric_id, trip_id=trip_id, now=now
        )
    finally:
        reset_current_tenant_id(token)


async def _consolidate_snapshot(
    tenant_id: uuid.UUID, *, snapshot_id: uuid.UUID, indicator_ids: list[uuid.UUID], now: datetime,
) -> None:
    token = set_current_tenant_id(tenant_id)
    try:
        await AnalyticsCalculationEngine().consolidate_snapshot(
            snapshot_id=snapshot_id, indicator_ids=indicator_ids, now=now
        )
    finally:
        reset_current_tenant_id(token)


async def _upload_file(client: AsyncClient, headers: dict[str, str], content: bytes) -> str:
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
    return body["file_id"]


# --------------------------------------------------------------------------------------
# Auditoria 1 + 2 — versão de Métrica respeitada pelo Indicador já calculado; `formula` nunca
# aparece na resposta do Indicador Consolidado.
# --------------------------------------------------------------------------------------


class TestMetricVersioningAudit:
    async def test_indicator_keeps_old_metric_version_after_formula_bump(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        metric_v1 = await _create_metric(client, headers)
        assert metric_v1["version"] == 1
        metric_v1_id = uuid.UUID(metric_v1["id"])

        trip_id = await _create_trip_with_revenue(client, headers, tenant_id, value=Decimal("1500.00"))
        now = datetime.now(timezone.utc)
        indicator = await _calculate_indicator(tenant_id, metric_id=metric_v1_id, trip_id=uuid.UUID(trip_id), now=now)

        get_indicator = await client.get(f"/api/v1/analytics/indicators/{indicator.id}", headers=headers)
        assert get_indicator.status_code == 200, get_indicator.text
        body = get_indicator.json()
        assert body["metric_id"] == str(metric_v1_id)
        assert body["metric_version"] == 1
        # Auditoria 2 — nunca inclui a fórmula.
        assert "formula" not in body

        # D155/D419 — mudar a fórmula cria uma NOVA linha física (D419), nunca um UPDATE.
        bump = await client.patch(
            f"/api/v1/analytics/metrics/{metric_v1_id}", headers=headers,
            json={"formula": "SUM(receita_realizada) * 1.1"},
        )
        assert bump.status_code == 200, bump.text
        metric_v2 = bump.json()
        assert metric_v2["version"] == 2
        assert metric_v2["id"] != str(metric_v1_id)

        # A versão antiga continua intocada.
        get_v1 = await client.get(f"/api/v1/analytics/metrics/{metric_v1_id}", headers=headers)
        assert get_v1.status_code == 200
        assert get_v1.json()["version"] == 1
        assert get_v1.json()["formula"] == "SUM(receita_realizada)"

        # Auditoria 1 — o Indicador já calculado continua referenciando a versão 1, mesmo depois
        # do bump.
        get_indicator_again = await client.get(f"/api/v1/analytics/indicators/{indicator.id}", headers=headers)
        assert get_indicator_again.status_code == 200
        assert get_indicator_again.json()["metric_id"] == str(metric_v1_id)
        assert get_indicator_again.json()["metric_version"] == 1


# --------------------------------------------------------------------------------------
# Auditoria 3 + 4 — Snapshot imutável depois de CONSOLIDADO; correção de receita_realizada não
# altera Indicador já SNAPSHOTADO.
# --------------------------------------------------------------------------------------


class TestSnapshotImmutabilityAudit:
    async def test_snapshot_consolidation_and_immutability(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        metric = await _create_metric(client, headers)
        metric_id = uuid.UUID(metric["id"])
        trip_id = await _create_trip_with_revenue(client, headers, tenant_id, value=Decimal("2000.00"))
        now = datetime.now(timezone.utc)

        indicator = await _calculate_indicator(tenant_id, metric_id=metric_id, trip_id=uuid.UUID(trip_id), now=now)
        assert indicator.valor == Decimal("2000.00")

        reference_period = now.date().isoformat()
        create_snapshot = await client.post(
            "/api/v1/analytics/snapshots", headers=headers, json={"reference_period": reference_period}
        )
        assert create_snapshot.status_code == 201, create_snapshot.text
        snapshot_id = uuid.UUID(create_snapshot.json()["id"])
        assert create_snapshot.json()["status"] == "EM_PROCESSAMENTO"

        await _consolidate_snapshot(tenant_id, snapshot_id=snapshot_id, indicator_ids=[indicator.id], now=now)

        get_snapshot = await client.get(f"/api/v1/analytics/snapshots/{snapshot_id}", headers=headers)
        assert get_snapshot.status_code == 200, get_snapshot.text
        snapshot_body = get_snapshot.json()
        assert snapshot_body["status"] == "CONSOLIDADO"
        assert snapshot_body["consolidated_at"] is not None
        assert str(indicator.id) in snapshot_body["indicator_ids"]
        assert snapshot_body["participating_metrics"] == [
            {"metric_id": str(metric_id), "metric_version": 1}
        ]

        get_indicator = await client.get(f"/api/v1/analytics/indicators/{indicator.id}", headers=headers)
        assert get_indicator.json()["status"] == "SNAPSHOTADO"
        assert get_indicator.json()["value"] == "2000.0000" or Decimal(get_indicator.json()["value"]) == Decimal("2000.00")

        # Auditoria 3 — recalcular um Indicador já SNAPSHOTADO é recusado.
        with pytest.raises(ConflictError) as excinfo:
            await _calculate_indicator(tenant_id, metric_id=metric_id, trip_id=uuid.UUID(trip_id), now=now)
        assert excinfo.value.code == "ANALYTICS_INDICATOR_SNAPSHOTTED"

        # Auditoria 4 — corrigir a receita realizada da Viagem DEPOIS do snapshot não pode alterar
        # o valor do Indicador já SNAPSHOTADO.
        await _correct_trip_revenue(tenant_id, trip_id, value=Decimal("9999.99"))
        get_indicator_after_correction = await client.get(
            f"/api/v1/analytics/indicators/{indicator.id}", headers=headers
        )
        assert Decimal(get_indicator_after_correction.json()["value"]) == Decimal("2000.00")


# --------------------------------------------------------------------------------------
# Auditoria 5 — Dashboard nunca armazena valor numérico de indicador, só configuração/referência.
# --------------------------------------------------------------------------------------


class TestDashboardConfigOnlyAudit:
    async def test_dashboard_stores_only_configuration_and_sharing_visibility(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        owner_headers, tenant_id = await _full_access_actor(client, tenants)
        metric = await _create_metric(client, headers=owner_headers)

        widgets = [{"metric_id": metric["id"], "chart_type": "LINE"}]
        create = await client.post(
            "/api/v1/reporting/dashboards", headers=owner_headers,
            json={"name": f"Painel {uuid.uuid4().hex[:6]}", "layout": {"columns": 2}, "widgets": widgets},
        )
        assert create.status_code == 201, create.text
        body = create.json()
        dashboard_id = body["id"]

        # Auditoria 5 — nenhuma chave numérica de valor é injetada; os widgets voltam exatamente
        # como enviados. D422 — sem `audit`.
        assert body["widgets"] == widgets
        assert "value" not in body and "valor" not in body
        assert "audit" not in body
        assert body["sharing"] == "PRIVADO"

        # Sem view_own/view_shared, um segundo usuário não vê o Dashboard privado do dono.
        viewer_headers = await _user_with_permissions(client, tenant_id, VIEW_SHARED_CODES)
        forbidden = await client.get(f"/api/v1/reporting/dashboards/{dashboard_id}", headers=viewer_headers)
        assert forbidden.status_code == 403

        share = await client.post(
            f"/api/v1/reporting/dashboards/{dashboard_id}/commands/share", headers=owner_headers,
            json={"sharing": "COMPARTILHADO_COM_PAPEL"},
        )
        assert share.status_code == 200, share.text
        assert share.json()["sharing"] == "COMPARTILHADO_COM_PAPEL"

        now_visible = await client.get(f"/api/v1/reporting/dashboards/{dashboard_id}", headers=viewer_headers)
        assert now_visible.status_code == 200

        listing = await client.get("/api/v1/reporting/dashboards", headers=viewer_headers)
        assert listing.status_code == 200
        assert any(d["id"] == dashboard_id for d in listing.json()["data"])

        # Um terceiro usuário com `view_own` mas SEM `view_shared` continua sem acesso, mesmo
        # depois do compartilhamento.
        view_own_only_headers = await _user_with_permissions(client, tenant_id, VIEW_OWN_ONLY_CODES)
        still_forbidden = await client.get(
            f"/api/v1/reporting/dashboards/{dashboard_id}", headers=view_own_only_headers
        )
        assert still_forbidden.status_code == 403

        # D422 — DELETE é soft delete via status=ARQUIVADO, dono continua enxergando.
        delete_resp = await client.delete(f"/api/v1/reporting/dashboards/{dashboard_id}", headers=owner_headers)
        assert delete_resp.status_code == 204
        get_after_delete = await client.get(f"/api/v1/reporting/dashboards/{dashboard_id}", headers=owner_headers)
        assert get_after_delete.status_code == 200
        assert get_after_delete.json()["status"] == "ARQUIVADO"


# --------------------------------------------------------------------------------------
# Auditoria 6 — isolamento por tenant; Platform Reference Data (D046) visível a todos os tenants.
# --------------------------------------------------------------------------------------


class TestTenantIsolationAndPlatformReferenceDataAudit:
    async def test_metric_tenant_isolation_and_platform_reference_data(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, tenant_a = await _full_access_actor(client, tenants)
        headers_b, tenant_b = await _full_access_actor(client, tenants)

        metric_a = await _create_metric(client, headers_a, name=f"Métrica Privada A {uuid.uuid4().hex[:6]}")

        # Tenant B nunca enxerga a Métrica privada do Tenant A.
        cross_tenant_get = await client.get(f"/api/v1/analytics/metrics/{metric_a['id']}", headers=headers_b)
        assert cross_tenant_get.status_code == 404

        # Platform Reference Data (`tenant_id IS NULL`) — inserida diretamente (não existe rota
        # HTTP para criar Reference Data; `CreateMetricHandler` sempre grava `actor.tenant_id`).
        session_factory = get_session_factory()
        platform_metric_id = uuid.uuid4()
        async with session_factory() as session:
            session.add(
                MetricModel(
                    id=platform_metric_id, tenant_id=None, nome=f"Métrica de Plataforma {uuid.uuid4().hex[:6]}",
                    formula="SUM(receita_realizada)", versao=1, granularidade_temporal="DIARIO",
                    granularidade_dimensional="TENANT", unidade="BRL", origem_dados={},
                    periodicidade_calculo="MANUAL", status="ATIVA",
                )
            )
            await session.commit()
        try:
            visible_to_a = await client.get(f"/api/v1/analytics/metrics/{platform_metric_id}", headers=headers_a)
            visible_to_b = await client.get(f"/api/v1/analytics/metrics/{platform_metric_id}", headers=headers_b)
            assert visible_to_a.status_code == 200
            assert visible_to_b.status_code == 200
        finally:
            async with session_factory() as session:
                await session.execute(delete(MetricModel).where(MetricModel.id == platform_metric_id))
                await session.commit()


# --------------------------------------------------------------------------------------
# Auditoria 7 — Exportação com erro sempre rastreável (`error_message` obrigatório e não vazio).
# --------------------------------------------------------------------------------------


class TestExportFailureTraceableAudit:
    async def test_export_failure_requires_error_message_and_complete_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id = await _full_access_actor(client, tenants)
        metric = await _create_metric(client, headers)

        create_report = await client.post(
            "/api/v1/reporting/saved-reports", headers=headers,
            json={
                "name": f"Relatório {uuid.uuid4().hex[:6]}", "metric_ids": [metric["id"]],
                "filters": {"status": "ATIVA"}, "output_format": "PDF",
            },
        )
        assert create_report.status_code == 201, create_report.text
        report_id = create_report.json()["id"]

        # D157 — o cliente tenta enviar filtros próprios junto com `saved_report_id`; a aplicação
        # ignora e resolve os filtros REAIS do Relatório Salvo no momento da chamada.
        create_export = await client.post(
            "/api/v1/reporting/exports", headers=headers,
            json={"saved_report_id": report_id, "filters": {"tampered": "true"}, "period": "2026-08"},
        )
        assert create_export.status_code == 201, create_export.text
        export_body = create_export.json()
        assert export_body["filters_used"] == {"status": "ATIVA"}
        assert export_body["metric_versions"] == [{"metric_id": metric["id"], "version": 1}]
        assert export_body["status"] == "PROCESSANDO"
        export_id = uuid.UUID(export_body["id"])

        token = set_current_tenant_id(tenant_id)
        try:
            with pytest.raises(ValueError):
                await ReportingInternalTransitions().fail_export(export_id=export_id, error_message="")

            await ReportingInternalTransitions().fail_export(
                export_id=export_id, error_message="Falha simulada ao gerar PDF."
            )
        finally:
            reset_current_tenant_id(token)
        get_failed = await client.get(f"/api/v1/reporting/exports/{export_id}", headers=headers)
        assert get_failed.status_code == 200
        failed_body = get_failed.json()
        assert failed_body["status"] == "FALHOU"
        assert failed_body["error_message"] == "Falha simulada ao gerar PDF."
        assert failed_body["file_id"] is None

        # D307/D308 — ciclo feliz completo, para D352 (cobertura de `complete_export` também).
        create_export_2 = await client.post(
            "/api/v1/reporting/exports", headers=headers, json={"saved_report_id": report_id, "period": "2026-08"},
        )
        assert create_export_2.status_code == 201, create_export_2.text
        export_id_2 = uuid.UUID(create_export_2.json()["id"])
        file_id = uuid.UUID(await _upload_file(client, headers, b"conteudo do relatorio exportado"))

        token = set_current_tenant_id(tenant_id)
        try:
            await ReportingInternalTransitions().complete_export(export_id=export_id_2, file_id=file_id)
        finally:
            reset_current_tenant_id(token)
        get_completed = await client.get(f"/api/v1/reporting/exports/{export_id_2}", headers=headers)
        assert get_completed.status_code == 200
        completed_body = get_completed.json()
        assert completed_body["status"] == "CONCLUIDA"
        assert completed_body["file_id"] == str(file_id)
        assert completed_body["error_message"] is None

        # Exportação avulsa (sem saved_report_id) exige filtros diretamente.
        missing_filters = await client.post("/api/v1/reporting/exports", headers=headers, json={})
        assert missing_filters.status_code == 400
        assert missing_filters.json()["error"]["code"] == "REPORTING_EXPORT_FILTERS_REQUIRED"


# --------------------------------------------------------------------------------------
# D352 — ciclo de vida completo de SavedFilter/ScheduledUpdate (CRUD, CHECK constraint D159/`ck_
# agendamentos_atualizacao_alvo`).
# --------------------------------------------------------------------------------------


class TestReportingCrudLifecycle:
    async def test_saved_filter_full_lifecycle(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/reporting/saved-filters", headers=headers,
            json={"name": f"Filtro {uuid.uuid4().hex[:6]}", "criteria": {"status": "ATIVA"}},
        )
        assert create.status_code == 201, create.text
        filter_id = create.json()["id"]

        update = await client.patch(
            f"/api/v1/reporting/saved-filters/{filter_id}", headers=headers,
            json={"criteria": {"status": "ARQUIVADA"}},
        )
        assert update.status_code == 200
        assert update.json()["criteria"] == {"status": "ARQUIVADA"}

        delete_resp = await client.delete(f"/api/v1/reporting/saved-filters/{filter_id}", headers=headers)
        assert delete_resp.status_code == 204

        get_after_delete = await client.get(f"/api/v1/reporting/saved-filters/{filter_id}", headers=headers)
        assert get_after_delete.status_code == 200
        assert get_after_delete.json()["status"] == "ARQUIVADO"

    async def test_scheduled_update_target_check_constraint(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _ = await _full_access_actor(client, tenants)
        metric = await _create_metric(client, headers)

        neither = await client.post(
            "/api/v1/reporting/scheduled-updates", headers=headers, json={"mode": "DIARIO"}
        )
        assert neither.status_code == 400
        assert neither.json()["error"]["code"] == "REPORTING_SCHEDULED_UPDATE_TARGET_REQUIRED"

        both = await client.post(
            "/api/v1/reporting/scheduled-updates", headers=headers,
            json={"metric_id": metric["id"], "cube_id": str(uuid.uuid4()), "mode": "DIARIO"},
        )
        assert both.status_code in (400, 404)

        valid = await client.post(
            "/api/v1/reporting/scheduled-updates", headers=headers,
            json={"metric_id": metric["id"], "mode": "DIARIO"},
        )
        assert valid.status_code == 201, valid.text
        scheduled_update_id = valid.json()["id"]

        update = await client.patch(
            f"/api/v1/reporting/scheduled-updates/{scheduled_update_id}", headers=headers,
            json={"mode": "MANUAL"},
        )
        assert update.status_code == 200
        assert update.json()["mode"] == "MANUAL"
        # O alvo não é editável — continua o mesmo metric_id.
        assert update.json()["metric_id"] == metric["id"]
