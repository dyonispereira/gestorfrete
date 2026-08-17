from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.analytics.domain.entities.consolidated_indicator import ConsolidatedIndicator
from modules.analytics.domain.repositories.consolidated_indicator_repository import (
    ConsolidatedIndicatorRepository,
)
from modules.analytics.domain.value_objects.indicator_status import IndicatorStatus
from modules.analytics.infrastructure.persistence.models.consolidated_indicator_model import (
    ConsolidatedIndicatorModel,
)


def _to_entity(model: ConsolidatedIndicatorModel) -> ConsolidatedIndicator:
    return ConsolidatedIndicator(
        id=model.id, metrica_id=model.metrica_id, metrica_versao=model.metrica_versao,
        dimensao_tipo=model.dimensao_tipo, dimensao_id=model.dimensao_id,
        periodo_referencia=model.periodo_referencia, valor=model.valor, data_hora_calculo=model.data_hora_calculo,
        status=IndicatorStatus(model.status),
    )


class SqlAlchemyConsolidatedIndicatorRepository(ConsolidatedIndicatorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ConsolidatedIndicator | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ConsolidatedIndicatorModel).where(
            ConsolidatedIndicatorModel.id == id, ConsolidatedIndicatorModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_latest(
        self, *, metrica_id: uuid.UUID, dimensao_tipo: str, dimensao_id: uuid.UUID, periodo_referencia: str
    ) -> ConsolidatedIndicator | None:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(ConsolidatedIndicatorModel)
            .where(
                ConsolidatedIndicatorModel.tenant_id == tenant_id,
                ConsolidatedIndicatorModel.metrica_id == metrica_id,
                ConsolidatedIndicatorModel.dimensao_tipo == dimensao_tipo,
                ConsolidatedIndicatorModel.dimensao_id == dimensao_id,
                ConsolidatedIndicatorModel.periodo_referencia == periodo_referencia,
            )
            .order_by(ConsolidatedIndicatorModel.data_hora_calculo.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, metric_id: uuid.UUID | None, dimension_type: str | None,
        dimension_id: uuid.UUID | None, reference_period: str | None, status: str | None,
    ) -> tuple[list[ConsolidatedIndicator], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ConsolidatedIndicatorModel).where(ConsolidatedIndicatorModel.tenant_id == tenant_id)
        if metric_id is not None:
            stmt = stmt.where(ConsolidatedIndicatorModel.metrica_id == metric_id)
        if dimension_type is not None:
            stmt = stmt.where(ConsolidatedIndicatorModel.dimensao_tipo == dimension_type)
        if dimension_id is not None:
            stmt = stmt.where(ConsolidatedIndicatorModel.dimensao_id == dimension_id)
        if reference_period is not None:
            stmt = stmt.where(ConsolidatedIndicatorModel.periodo_referencia == reference_period)
        if status is not None:
            stmt = stmt.where(ConsolidatedIndicatorModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ConsolidatedIndicatorModel.data_hora_calculo.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, indicator: ConsolidatedIndicator) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ConsolidatedIndicatorModel, indicator.id)
        if model is None:
            model = ConsolidatedIndicatorModel(id=indicator.id, tenant_id=tenant_id)
            self._session.add(model)
        model.metrica_id = indicator.metrica_id
        model.metrica_versao = indicator.metrica_versao
        model.dimensao_tipo = indicator.dimensao_tipo
        model.dimensao_id = indicator.dimensao_id
        model.periodo_referencia = indicator.periodo_referencia
        model.valor = indicator.valor
        model.data_hora_calculo = indicator.data_hora_calculo
        model.status = indicator.status.value
        await self._session.flush()
