from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.reporting.domain.entities.scheduled_update import ScheduledUpdate
from modules.reporting.domain.repositories.scheduled_update_repository import ScheduledUpdateRepository
from modules.reporting.domain.value_objects.scheduled_update_mode import ScheduledUpdateMode
from modules.reporting.infrastructure.persistence.models.scheduled_update_model import ScheduledUpdateModel


def _to_entity(model: ScheduledUpdateModel) -> ScheduledUpdate:
    return ScheduledUpdate(
        id=model.id, tenant_id=model.tenant_id, metrica_id=model.metrica_id,
        cubo_analitico_id=model.cubo_analitico_id, modo=ScheduledUpdateMode(model.modo), status=model.status,
    )


class SqlAlchemyScheduledUpdateRepository(ScheduledUpdateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ScheduledUpdate | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ScheduledUpdateModel).where(
            ScheduledUpdateModel.id == id, ScheduledUpdateModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, metric_id: uuid.UUID | None, cube_id: uuid.UUID | None, mode: str | None,
        status: str | None,
    ) -> tuple[list[ScheduledUpdate], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ScheduledUpdateModel).where(ScheduledUpdateModel.tenant_id == tenant_id)
        if metric_id is not None:
            stmt = stmt.where(ScheduledUpdateModel.metrica_id == metric_id)
        if cube_id is not None:
            stmt = stmt.where(ScheduledUpdateModel.cubo_analitico_id == cube_id)
        if mode is not None:
            stmt = stmt.where(ScheduledUpdateModel.modo == mode)
        if status is not None:
            stmt = stmt.where(ScheduledUpdateModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, scheduled_update: ScheduledUpdate) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ScheduledUpdateModel, scheduled_update.id)
        if model is None:
            model = ScheduledUpdateModel(id=scheduled_update.id, tenant_id=tenant_id)
            self._session.add(model)
        model.metrica_id = scheduled_update.metrica_id
        model.cubo_analitico_id = scheduled_update.cubo_analitico_id
        model.modo = scheduled_update.modo.value
        model.status = scheduled_update.status
        await self._session.flush()
