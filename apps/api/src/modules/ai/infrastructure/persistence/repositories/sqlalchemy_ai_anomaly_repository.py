from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_anomaly import AIAnomaly
from modules.ai.domain.repositories.ai_anomaly_repository import AIAnomalyRepository
from modules.ai.domain.value_objects.anomaly_status import AnomalyStatus
from modules.ai.infrastructure.persistence.models.ai_anomaly_model import AIAnomalyModel


def _to_entity(model: AIAnomalyModel) -> AIAnomaly:
    return AIAnomaly(
        id=model.id, tenant_id=model.tenant_id, inferencia_ia_id=model.inferencia_ia_id,
        leitura_origem_tipo=model.leitura_origem_tipo, leitura_origem_id=model.leitura_origem_id,
        nivel_confianca=model.nivel_confianca, status=AnomalyStatus(model.status),
    )


class SqlAlchemyAIAnomalyRepository(AIAnomalyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIAnomaly | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIAnomalyModel).where(AIAnomalyModel.id == id, AIAnomalyModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, leitura_origem_tipo: str | None, status: str | None,
    ) -> tuple[list[AIAnomaly], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIAnomalyModel).where(AIAnomalyModel.tenant_id == tenant_id)
        if leitura_origem_tipo is not None:
            stmt = stmt.where(AIAnomalyModel.leitura_origem_tipo == leitura_origem_tipo)
        if status is not None:
            stmt = stmt.where(AIAnomalyModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AIAnomalyModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, anomaly: AIAnomaly) -> None:
        model = await self._session.get(AIAnomalyModel, anomaly.id)
        if model is None:
            model = AIAnomalyModel(id=anomaly.id, tenant_id=anomaly.tenant_id)
            self._session.add(model)
        model.inferencia_ia_id = anomaly.inferencia_ia_id
        model.leitura_origem_tipo = anomaly.leitura_origem_tipo
        model.leitura_origem_id = anomaly.leitura_origem_id
        model.nivel_confianca = anomaly.nivel_confianca
        model.status = anomaly.status.value
        await self._session.flush()
