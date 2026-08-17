from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.reporting.domain.entities.saved_filter import SavedFilter
from modules.reporting.domain.repositories.saved_filter_repository import SavedFilterRepository
from modules.reporting.infrastructure.persistence.models.saved_filter_model import SavedFilterModel


def _to_entity(model: SavedFilterModel) -> SavedFilter:
    return SavedFilter(id=model.id, usuario_id=model.usuario_id, nome=model.nome, criterios=model.criterios, status=model.status)


class SqlAlchemySavedFilterRepository(SavedFilterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> SavedFilter | None:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedFilterModel).where(SavedFilterModel.id == id, SavedFilterModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_name(self, usuario_id: uuid.UUID, nome: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedFilterModel.id).where(
            SavedFilterModel.tenant_id == tenant_id, SavedFilterModel.usuario_id == usuario_id,
            SavedFilterModel.nome == nome,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, status: str | None, usuario_id: uuid.UUID
    ) -> tuple[list[SavedFilter], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedFilterModel).where(
            SavedFilterModel.tenant_id == tenant_id, SavedFilterModel.usuario_id == usuario_id
        )
        if search is not None:
            stmt = stmt.where(SavedFilterModel.nome.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(SavedFilterModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SavedFilterModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, saved_filter: SavedFilter) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(SavedFilterModel, saved_filter.id)
        if model is None:
            model = SavedFilterModel(id=saved_filter.id, tenant_id=tenant_id)
            self._session.add(model)
        model.usuario_id = saved_filter.usuario_id
        model.nome = saved_filter.nome
        model.criterios = saved_filter.criterios
        model.status = saved_filter.status
        await self._session.flush()
