from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_feedback import AIFeedback
from modules.ai.domain.repositories.ai_feedback_repository import AIFeedbackRepository
from modules.ai.domain.value_objects.feedback_output_type import FeedbackOutputType
from modules.ai.domain.value_objects.feedback_result import FeedbackResult
from modules.ai.infrastructure.persistence.models.ai_feedback_model import AIFeedbackModel


def _to_entity(model: AIFeedbackModel) -> AIFeedback:
    return AIFeedback(
        id=model.id, tenant_id=model.tenant_id, saida_ia_tipo=FeedbackOutputType(model.saida_ia_tipo),
        saida_ia_id=model.saida_ia_id, usuario_id=model.usuario_id, resultado=FeedbackResult(model.resultado),
        justificativa=model.justificativa, resultado_real=model.resultado_real, criado_em=model.criado_em,
    )


class SqlAlchemyAIFeedbackRepository(AIFeedbackRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIFeedback | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIFeedbackModel).where(AIFeedbackModel.id == id, AIFeedbackModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, saida_ia_tipo: str | None, saida_ia_id: uuid.UUID | None,
        resultado: str | None,
    ) -> tuple[list[AIFeedback], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIFeedbackModel).where(AIFeedbackModel.tenant_id == tenant_id)
        if saida_ia_tipo is not None:
            stmt = stmt.where(AIFeedbackModel.saida_ia_tipo == saida_ia_tipo)
        if saida_ia_id is not None:
            stmt = stmt.where(AIFeedbackModel.saida_ia_id == saida_ia_id)
        if resultado is not None:
            stmt = stmt.where(AIFeedbackModel.resultado == resultado)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AIFeedbackModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, feedback: AIFeedback) -> None:
        model = await self._session.get(AIFeedbackModel, feedback.id)
        if model is None:
            model = AIFeedbackModel(id=feedback.id, tenant_id=feedback.tenant_id, criado_em=feedback.criado_em)
            self._session.add(model)
        model.saida_ia_tipo = feedback.saida_ia_tipo.value
        model.saida_ia_id = feedback.saida_ia_id
        model.usuario_id = feedback.usuario_id
        model.resultado = feedback.resultado.value
        model.justificativa = feedback.justificativa
        model.resultado_real = feedback.resultado_real
        await self._session.flush()
