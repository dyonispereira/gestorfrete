from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.speed_limit_config import SpeedLimitConfig
from modules.tracking.domain.repositories.speed_limit_config_repository import SpeedLimitConfigRepository
from modules.tracking.domain.value_objects.speed_limit_config_status import SpeedLimitConfigStatus
from modules.tracking.infrastructure.persistence.models.speed_limit_config_model import SpeedLimitConfigModel


def _to_entity(model: SpeedLimitConfigModel) -> SpeedLimitConfig:
    return SpeedLimitConfig(
        id=model.id, categoria_veiculo_id=model.categoria_veiculo_id, limite_kmh=float(model.limite_kmh),
        status=SpeedLimitConfigStatus(model.status),
    )


class SqlAlchemySpeedLimitConfigRepository(SpeedLimitConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> SpeedLimitConfig | None:
        tenant_id = get_current_tenant_id()
        stmt = select(SpeedLimitConfigModel).where(
            SpeedLimitConfigModel.id == id, SpeedLimitConfigModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_applicable(self, categoria_veiculo_id: uuid.UUID | None) -> SpeedLimitConfig | None:
        tenant_id = get_current_tenant_id()
        if categoria_veiculo_id is not None:
            stmt = select(SpeedLimitConfigModel).where(
                SpeedLimitConfigModel.tenant_id == tenant_id,
                SpeedLimitConfigModel.categoria_veiculo_id == categoria_veiculo_id,
                SpeedLimitConfigModel.status == SpeedLimitConfigStatus.ATIVA.value,
            )
            model = (await self._session.execute(stmt)).scalar_one_or_none()
            if model is not None:
                return _to_entity(model)

        default_stmt = select(SpeedLimitConfigModel).where(
            SpeedLimitConfigModel.tenant_id == tenant_id, SpeedLimitConfigModel.categoria_veiculo_id.is_(None),
            SpeedLimitConfigModel.status == SpeedLimitConfigStatus.ATIVA.value,
        )
        default_model = (await self._session.execute(default_stmt)).scalar_one_or_none()
        return _to_entity(default_model) if default_model is not None else None

    async def list_page(
        self, *, page: int, limit: int, vehicle_category_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[SpeedLimitConfig], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(SpeedLimitConfigModel).where(SpeedLimitConfigModel.tenant_id == tenant_id)
        if vehicle_category_id is not None:
            stmt = stmt.where(SpeedLimitConfigModel.categoria_veiculo_id == vehicle_category_id)
        if status is not None:
            stmt = stmt.where(SpeedLimitConfigModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SpeedLimitConfigModel.limite_kmh.asc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, config: SpeedLimitConfig) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(SpeedLimitConfigModel, config.id)
        if model is None:
            model = SpeedLimitConfigModel(id=config.id, tenant_id=tenant_id)
            self._session.add(model)
        model.categoria_veiculo_id = config.categoria_veiculo_id
        model.limite_kmh = config.limite_kmh
        model.status = config.status.value
        await self._session.flush()
