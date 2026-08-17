from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.analytics.domain.entities.analytical_snapshot import AnalyticalSnapshot
from modules.analytics.domain.repositories.analytical_snapshot_repository import AnalyticalSnapshotRepository
from modules.analytics.domain.value_objects.snapshot_processing_origin import SnapshotProcessingOrigin
from modules.analytics.domain.value_objects.snapshot_status import SnapshotStatus
from modules.analytics.infrastructure.persistence.models.analytical_snapshot_model import (
    AnalyticalSnapshotIndicatorModel,
    AnalyticalSnapshotModel,
)
from modules.analytics.infrastructure.persistence.models.consolidated_indicator_model import (
    ConsolidatedIndicatorModel,
)


def _to_entity(model: AnalyticalSnapshotModel) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        id=model.id, tenant_id=model.tenant_id, periodo_referencia=model.periodo_referencia,
        data_hora_consolidacao=model.data_hora_consolidacao,
        origem_processamento=SnapshotProcessingOrigin(model.origem_processamento), usuario_id=model.usuario_id,
        status=SnapshotStatus(model.status),
    )


class SqlAlchemyAnalyticalSnapshotRepository(AnalyticalSnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AnalyticalSnapshot | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AnalyticalSnapshotModel).where(
            AnalyticalSnapshotModel.id == id, AnalyticalSnapshotModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_consolidated_for_period(self, periodo_referencia: str) -> AnalyticalSnapshot | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AnalyticalSnapshotModel).where(
            AnalyticalSnapshotModel.tenant_id == tenant_id,
            AnalyticalSnapshotModel.periodo_referencia == periodo_referencia,
            AnalyticalSnapshotModel.status == SnapshotStatus.CONSOLIDADO.value,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, reference_period: str | None, processing_origin: str | None,
        status: str | None,
    ) -> tuple[list[AnalyticalSnapshot], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AnalyticalSnapshotModel).where(AnalyticalSnapshotModel.tenant_id == tenant_id)
        if reference_period is not None:
            stmt = stmt.where(AnalyticalSnapshotModel.periodo_referencia == reference_period)
        if processing_origin is not None:
            stmt = stmt.where(AnalyticalSnapshotModel.origem_processamento == processing_origin)
        if status is not None:
            stmt = stmt.where(AnalyticalSnapshotModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnalyticalSnapshotModel.periodo_referencia.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def list_indicator_ids(self, snapshot_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(AnalyticalSnapshotIndicatorModel.indicador_consolidado_id).where(
            AnalyticalSnapshotIndicatorModel.snapshot_analitico_id == snapshot_id
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_participating_metrics(self, snapshot_id: uuid.UUID) -> list[tuple[uuid.UUID, int]]:
        stmt = (
            select(ConsolidatedIndicatorModel.metrica_id, ConsolidatedIndicatorModel.metrica_versao)
            .join(
                AnalyticalSnapshotIndicatorModel,
                AnalyticalSnapshotIndicatorModel.indicador_consolidado_id == ConsolidatedIndicatorModel.id,
            )
            .where(AnalyticalSnapshotIndicatorModel.snapshot_analitico_id == snapshot_id)
            .distinct()
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows]

    async def add(self, snapshot: AnalyticalSnapshot) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AnalyticalSnapshotModel, snapshot.id)
        if model is None:
            model = AnalyticalSnapshotModel(id=snapshot.id, tenant_id=tenant_id)
            self._session.add(model)
        model.periodo_referencia = snapshot.periodo_referencia
        model.data_hora_consolidacao = snapshot.data_hora_consolidacao
        model.origem_processamento = snapshot.origem_processamento.value
        model.usuario_id = snapshot.usuario_id
        model.status = snapshot.status.value
        await self._session.flush()

    async def link_indicators(self, snapshot_id: uuid.UUID, indicator_ids: list[uuid.UUID]) -> None:
        if not indicator_ids:
            return
        stmt = pg_insert(AnalyticalSnapshotIndicatorModel).values(
            [{"snapshot_analitico_id": snapshot_id, "indicador_consolidado_id": iid} for iid in indicator_ids]
        ).on_conflict_do_nothing(index_elements=["snapshot_analitico_id", "indicador_consolidado_id"])
        await self._session.execute(stmt)
        await self._session.flush()
