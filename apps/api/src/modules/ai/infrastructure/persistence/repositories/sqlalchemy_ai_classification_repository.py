from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_classification import AIClassification
from modules.ai.domain.repositories.ai_classification_repository import AIClassificationRepository
from modules.ai.domain.value_objects.classification_type import ClassificationType
from modules.ai.infrastructure.persistence.models.ai_classification_model import AIClassificationModel


def _to_entity(model: AIClassificationModel) -> AIClassification:
    return AIClassification(
        id=model.id, tenant_id=model.tenant_id, inferencia_ia_id=model.inferencia_ia_id,
        tipo_classificacao=ClassificationType(model.tipo_classificacao),
        entidade_alvo_tipo=model.entidade_alvo_tipo, entidade_alvo_id=model.entidade_alvo_id,
        rotulo=model.rotulo, nivel_confianca=model.nivel_confianca, criado_em=model.criado_em,
    )


class SqlAlchemyAIClassificationRepository(AIClassificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIClassification | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIClassificationModel).where(
            AIClassificationModel.id == id, AIClassificationModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, tipo_classificacao: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None,
    ) -> tuple[list[AIClassification], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIClassificationModel).where(AIClassificationModel.tenant_id == tenant_id)
        if tipo_classificacao is not None:
            stmt = stmt.where(AIClassificationModel.tipo_classificacao == tipo_classificacao)
        if entidade_alvo_tipo is not None:
            stmt = stmt.where(AIClassificationModel.entidade_alvo_tipo == entidade_alvo_tipo)
        if entidade_alvo_id is not None:
            stmt = stmt.where(AIClassificationModel.entidade_alvo_id == entidade_alvo_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AIClassificationModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, classification: AIClassification) -> None:
        model = await self._session.get(AIClassificationModel, classification.id)
        if model is None:
            model = AIClassificationModel(
                id=classification.id, tenant_id=classification.tenant_id, criado_em=classification.criado_em,
            )
            self._session.add(model)
        model.inferencia_ia_id = classification.inferencia_ia_id
        model.tipo_classificacao = classification.tipo_classificacao.value
        model.entidade_alvo_tipo = classification.entidade_alvo_tipo
        model.entidade_alvo_id = classification.entidade_alvo_id
        model.rotulo = classification.rotulo
        model.nivel_confianca = classification.nivel_confianca
        await self._session.flush()
