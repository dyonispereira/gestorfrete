from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.integration.domain.entities.integration_config import IntegrationConfig
from modules.integration.domain.repositories.integration_config_repository import IntegrationConfigRepository
from modules.integration.domain.value_objects.integration_config_status import IntegrationConfigStatus
from modules.integration.infrastructure.persistence.models.integration_config_model import IntegrationConfigModel


def _to_entity(model: IntegrationConfigModel) -> IntegrationConfig:
    return IntegrationConfig(
        id=model.id, tipo=model.tipo, credencial_arquivo_id=model.credencial_arquivo_id,
        status=IntegrationConfigStatus(model.status),
    )


class SqlAlchemyIntegrationConfigRepository(IntegrationConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> IntegrationConfig | None:
        tenant_id = get_current_tenant_id()
        stmt = select(IntegrationConfigModel).where(
            IntegrationConfigModel.id == id, IntegrationConfigModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, tipo: str | None, status: str | None
    ) -> tuple[list[IntegrationConfig], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(IntegrationConfigModel).where(IntegrationConfigModel.tenant_id == tenant_id)
        if tipo is not None:
            stmt = stmt.where(IntegrationConfigModel.tipo == tipo)
        if status is not None:
            stmt = stmt.where(IntegrationConfigModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, config: IntegrationConfig) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(IntegrationConfigModel, config.id)
        if model is None:
            model = IntegrationConfigModel(id=config.id, tenant_id=tenant_id)
            self._session.add(model)
        model.tipo = config.tipo
        model.credencial_arquivo_id = config.credencial_arquivo_id
        model.status = config.status.value
        await self._session.flush()
