from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.tracking_provider import TrackingProvider
from modules.tracking.domain.repositories.tracking_provider_repository import TrackingProviderRepository
from modules.tracking.domain.value_objects.tracking_provider_status import TrackingProviderStatus
from modules.tracking.infrastructure.persistence.models.tracking_provider_model import TrackingProviderModel


def _to_entity(model: TrackingProviderModel) -> TrackingProvider:
    return TrackingProvider(id=model.id, nome=model.nome, status=TrackingProviderStatus(model.status))


class SqlAlchemyTrackingProviderRepository(TrackingProviderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> TrackingProvider | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingProviderModel).where(
            TrackingProviderModel.id == id, TrackingProviderModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_nome(self, nome: str) -> TrackingProvider | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingProviderModel).where(
            TrackingProviderModel.tenant_id == tenant_id, TrackingProviderModel.nome == nome
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, status: str | None
    ) -> tuple[list[TrackingProvider], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingProviderModel).where(TrackingProviderModel.tenant_id == tenant_id)
        if search is not None:
            stmt = stmt.where(TrackingProviderModel.nome.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(TrackingProviderModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(TrackingProviderModel.nome.asc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, provider: TrackingProvider) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(TrackingProviderModel, provider.id)
        if model is None:
            model = TrackingProviderModel(id=provider.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome = provider.nome
        model.status = provider.status.value
        await self._session.flush()
