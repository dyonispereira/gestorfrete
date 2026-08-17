from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.analytics.domain.entities.analytics_cube import AnalyticsCube
from modules.analytics.domain.repositories.analytics_cube_repository import AnalyticsCubeRepository
from modules.analytics.infrastructure.persistence.models.analytics_cube_model import (
    AnalyticsCubeMetricModel,
    AnalyticsCubeModel,
)


class SqlAlchemyAnalyticsCubeRepository(AnalyticsCubeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _to_entity(self, model: AnalyticsCubeModel) -> AnalyticsCube:
        metric_ids_stmt = select(AnalyticsCubeMetricModel.metrica_id).where(
            AnalyticsCubeMetricModel.cubo_analitico_id == model.id
        )
        metric_ids = list((await self._session.execute(metric_ids_stmt)).scalars().all())
        return AnalyticsCube(
            id=model.id, tenant_id=model.tenant_id, nome=model.nome, dimensoes=list(model.dimensoes),
            metricas_ids=metric_ids, status=model.status,
        )

    async def get_by_id(self, id: uuid.UUID) -> AnalyticsCube | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AnalyticsCubeModel).where(AnalyticsCubeModel.id == id, AnalyticsCubeModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return await self._to_entity(model) if model is not None else None

    async def exists_with_name(
        self, tenant_id: uuid.UUID, nome: str, *, excluding_id: uuid.UUID | None = None
    ) -> bool:
        stmt = select(AnalyticsCubeModel.id).where(
            AnalyticsCubeModel.tenant_id == tenant_id, AnalyticsCubeModel.nome == nome
        )
        if excluding_id is not None:
            stmt = stmt.where(AnalyticsCubeModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, status: str | None
    ) -> tuple[list[AnalyticsCube], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AnalyticsCubeModel).where(AnalyticsCubeModel.tenant_id == tenant_id)
        if search is not None:
            stmt = stmt.where(AnalyticsCubeModel.nome.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(AnalyticsCubeModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnalyticsCubeModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [await self._to_entity(m) for m in models], total

    async def add(self, cube: AnalyticsCube) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AnalyticsCubeModel, cube.id)
        if model is None:
            model = AnalyticsCubeModel(id=cube.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome = cube.nome
        model.dimensoes = cube.dimensoes
        model.status = cube.status
        await self._session.flush()

        await self._session.execute(
            delete(AnalyticsCubeMetricModel).where(AnalyticsCubeMetricModel.cubo_analitico_id == cube.id)
        )
        if cube.metricas_ids:
            stmt = pg_insert(AnalyticsCubeMetricModel).values(
                [{"cubo_analitico_id": cube.id, "metrica_id": mid} for mid in cube.metricas_ids]
            ).on_conflict_do_nothing(index_elements=["cubo_analitico_id", "metrica_id"])
            await self._session.execute(stmt)
        await self._session.flush()
