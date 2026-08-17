from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_inference import AIInference
from modules.ai.domain.repositories.ai_inference_repository import AIInferenceRepository
from modules.ai.domain.value_objects.inference_origin import InferenceOrigin
from modules.ai.domain.value_objects.inference_status import InferenceStatus
from modules.ai.infrastructure.persistence.models.ai_inference_model import AIInferenceModel


def _to_entity(model: AIInferenceModel) -> AIInference:
    return AIInference(
        id=model.id, tenant_id=model.tenant_id, modelo_ia_id=model.modelo_ia_id,
        modelo_ia_versao=model.modelo_ia_versao, entrada=model.entrada, saida=model.saida,
        nivel_confianca=model.nivel_confianca, data_hora_inicio=model.data_hora_inicio,
        data_hora_fim=model.data_hora_fim, duracao_ms=model.duracao_ms, custo=model.custo,
        numero_tentativa=model.numero_tentativa, origem=InferenceOrigin(model.origem),
        status=InferenceStatus(model.status),
    )


class SqlAlchemyAIInferenceRepository(AIInferenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIInference | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIInferenceModel).where(AIInferenceModel.id == id, AIInferenceModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, cursor_data_hora: datetime | None, cursor_id: uuid.UUID | None, limit: int,
        modelo_ia_id: uuid.UUID | None, status: str | None, origem: str | None,
        started_at_from: datetime | None, started_at_to: datetime | None,
    ) -> list[AIInference]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIInferenceModel).where(AIInferenceModel.tenant_id == tenant_id)
        if modelo_ia_id is not None:
            stmt = stmt.where(AIInferenceModel.modelo_ia_id == modelo_ia_id)
        if status is not None:
            stmt = stmt.where(AIInferenceModel.status == status)
        if origem is not None:
            stmt = stmt.where(AIInferenceModel.origem == origem)
        if started_at_from is not None:
            stmt = stmt.where(AIInferenceModel.data_hora_inicio >= started_at_from)
        if started_at_to is not None:
            stmt = stmt.where(AIInferenceModel.data_hora_inicio <= started_at_to)
        if cursor_data_hora is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    AIInferenceModel.data_hora_inicio < cursor_data_hora,
                    and_(AIInferenceModel.data_hora_inicio == cursor_data_hora, AIInferenceModel.id < cursor_id),
                )
            )
        stmt = stmt.order_by(AIInferenceModel.data_hora_inicio.desc(), AIInferenceModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, inference: AIInference) -> None:
        model = AIInferenceModel(
            id=inference.id, tenant_id=inference.tenant_id, modelo_ia_id=inference.modelo_ia_id,
            modelo_ia_versao=inference.modelo_ia_versao, entrada=inference.entrada, saida=inference.saida,
            nivel_confianca=inference.nivel_confianca, data_hora_inicio=inference.data_hora_inicio,
            data_hora_fim=inference.data_hora_fim, custo=inference.custo,
            numero_tentativa=inference.numero_tentativa, origem=inference.origem.value,
            status=inference.status.value,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["duracao_ms"])
        inference.duracao_ms = model.duracao_ms
