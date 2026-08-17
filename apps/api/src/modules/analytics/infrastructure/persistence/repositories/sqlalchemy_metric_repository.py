from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.analytics.domain.entities.metric import Metric
from modules.analytics.domain.repositories.metric_repository import MetricRepository
from modules.analytics.domain.value_objects.metric_dimensional_granularity import MetricDimensionalGranularity
from modules.analytics.domain.value_objects.metric_periodicity import MetricPeriodicity
from modules.analytics.domain.value_objects.metric_status import MetricStatus
from modules.analytics.domain.value_objects.metric_temporal_granularity import MetricTemporalGranularity
from modules.analytics.infrastructure.persistence.models.metric_model import MetricModel


def _to_entity(model: MetricModel) -> Metric:
    return Metric(
        id=model.id, tenant_id=model.tenant_id, nome=model.nome, formula=model.formula, versao=model.versao,
        granularidade_temporal=MetricTemporalGranularity(model.granularidade_temporal),
        granularidade_dimensional=MetricDimensionalGranularity(model.granularidade_dimensional),
        unidade=model.unidade, origem_dados=model.origem_dados,
        periodicidade_calculo=MetricPeriodicity(model.periodicidade_calculo), status=MetricStatus(model.status),
    )


class SqlAlchemyMetricRepository(MetricRepository):
    """D046 — Platform Reference Data (`tenant_id IS NULL`) sempre visível, além do escopo do
    próprio tenant — a única leitura deste projeto que propositalmente amplia o filtro além de
    `get_current_tenant_id()`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Metric | None:
        tenant_id = get_current_tenant_id()
        stmt = select(MetricModel).where(
            MetricModel.id == id, or_(MetricModel.tenant_id == tenant_id, MetricModel.tenant_id.is_(None))
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_latest_by_name(self, nome: str, *, tenant_id: uuid.UUID | None) -> Metric | None:
        current_tenant_id = get_current_tenant_id()
        scope = tenant_id if tenant_id is not None else current_tenant_id
        stmt = (
            select(MetricModel)
            .where(MetricModel.nome == nome, or_(MetricModel.tenant_id == scope, MetricModel.tenant_id.is_(None)))
            .order_by(MetricModel.versao.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, temporal_granularity: str | None,
        dimensional_granularity: str | None, status: str | None,
    ) -> tuple[list[Metric], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(MetricModel).where(or_(MetricModel.tenant_id == tenant_id, MetricModel.tenant_id.is_(None)))
        if search is not None:
            stmt = stmt.where(MetricModel.nome.ilike(f"%{search}%"))
        if temporal_granularity is not None:
            stmt = stmt.where(MetricModel.granularidade_temporal == temporal_granularity)
        if dimensional_granularity is not None:
            stmt = stmt.where(MetricModel.granularidade_dimensional == dimensional_granularity)
        if status is not None:
            stmt = stmt.where(MetricModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(MetricModel.nome, MetricModel.versao.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, metric: Metric) -> None:
        tenant_id = metric.tenant_id if metric.tenant_id is not None else get_current_tenant_id()
        model = await self._session.get(MetricModel, metric.id)
        if model is None:
            model = MetricModel(id=metric.id, tenant_id=metric.tenant_id if metric.tenant_id is not None else tenant_id)
            self._session.add(model)
        model.nome = metric.nome
        model.formula = metric.formula
        model.versao = metric.versao
        model.granularidade_temporal = metric.granularidade_temporal.value
        model.granularidade_dimensional = metric.granularidade_dimensional.value
        model.unidade = metric.unidade
        model.origem_dados = metric.origem_dados
        model.periodicidade_calculo = metric.periodicidade_calculo.value
        model.status = metric.status.value
        await self._session.flush()
