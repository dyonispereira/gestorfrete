from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_prediction import AIPrediction
from modules.ai.domain.repositories.ai_prediction_repository import AIPredictionRepository
from modules.ai.domain.value_objects.prediction_status import PredictionStatus
from modules.ai.infrastructure.persistence.models.ai_prediction_model import AIPredictionModel


def _to_entity(model: AIPredictionModel) -> AIPrediction:
    return AIPrediction(
        id=model.id, tenant_id=model.tenant_id, inferencia_ia_id=model.inferencia_ia_id,
        categoria=model.categoria, entidade_alvo_tipo=model.entidade_alvo_tipo,
        entidade_alvo_id=model.entidade_alvo_id, valor_previsto=model.valor_previsto,
        nivel_confianca=model.nivel_confianca, data_hora_validade_fim=model.data_hora_validade_fim,
        status=PredictionStatus(model.status),
    )


class SqlAlchemyAIPredictionRepository(AIPredictionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIPrediction | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIPredictionModel).where(AIPredictionModel.id == id, AIPredictionModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, categoria: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None, include_expired: bool,
    ) -> tuple[list[AIPrediction], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIPredictionModel).where(AIPredictionModel.tenant_id == tenant_id)
        if categoria is not None:
            stmt = stmt.where(AIPredictionModel.categoria == categoria)
        if entidade_alvo_tipo is not None:
            stmt = stmt.where(AIPredictionModel.entidade_alvo_tipo == entidade_alvo_tipo)
        if entidade_alvo_id is not None:
            stmt = stmt.where(AIPredictionModel.entidade_alvo_id == entidade_alvo_id)
        if not include_expired:
            now = datetime.now(timezone.utc)
            stmt = stmt.where(AIPredictionModel.data_hora_validade_fim >= now)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AIPredictionModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, prediction: AIPrediction) -> None:
        model = await self._session.get(AIPredictionModel, prediction.id)
        if model is None:
            model = AIPredictionModel(id=prediction.id, tenant_id=prediction.tenant_id)
            self._session.add(model)
        model.inferencia_ia_id = prediction.inferencia_ia_id
        model.categoria = prediction.categoria
        model.entidade_alvo_tipo = prediction.entidade_alvo_tipo
        model.entidade_alvo_id = prediction.entidade_alvo_id
        model.valor_previsto = prediction.valor_previsto
        model.nivel_confianca = prediction.nivel_confianca
        model.data_hora_validade_fim = prediction.data_hora_validade_fim
        model.status = prediction.status.value
        await self._session.flush()
