from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_suggestion import AISuggestion
from modules.ai.domain.repositories.ai_suggestion_repository import AISuggestionRepository
from modules.ai.domain.value_objects.suggestion_status import SuggestionStatus
from modules.ai.infrastructure.persistence.models.ai_suggestion_model import AISuggestionModel


def _to_entity(model: AISuggestionModel) -> AISuggestion:
    return AISuggestion(
        id=model.id, tenant_id=model.tenant_id, inferencia_ia_id=model.inferencia_ia_id,
        categoria=model.categoria, entidade_alvo_tipo=model.entidade_alvo_tipo,
        entidade_alvo_id=model.entidade_alvo_id, recomendacao=model.recomendacao,
        justificativa=model.justificativa, nivel_confianca=model.nivel_confianca,
        status=SuggestionStatus(model.status), usuario_decisao_id=model.usuario_decisao_id,
        data_hora_decisao=model.data_hora_decisao,
    )


class SqlAlchemyAISuggestionRepository(AISuggestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AISuggestion | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AISuggestionModel).where(AISuggestionModel.id == id, AISuggestionModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, categoria: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None, status: str | None,
    ) -> tuple[list[AISuggestion], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AISuggestionModel).where(AISuggestionModel.tenant_id == tenant_id)
        if categoria is not None:
            stmt = stmt.where(AISuggestionModel.categoria == categoria)
        if entidade_alvo_tipo is not None:
            stmt = stmt.where(AISuggestionModel.entidade_alvo_tipo == entidade_alvo_tipo)
        if entidade_alvo_id is not None:
            stmt = stmt.where(AISuggestionModel.entidade_alvo_id == entidade_alvo_id)
        if status is not None:
            stmt = stmt.where(AISuggestionModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AISuggestionModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, suggestion: AISuggestion) -> None:
        model = await self._session.get(AISuggestionModel, suggestion.id)
        if model is None:
            model = AISuggestionModel(id=suggestion.id, tenant_id=suggestion.tenant_id)
            self._session.add(model)
        model.inferencia_ia_id = suggestion.inferencia_ia_id
        model.categoria = suggestion.categoria
        model.entidade_alvo_tipo = suggestion.entidade_alvo_tipo
        model.entidade_alvo_id = suggestion.entidade_alvo_id
        model.recomendacao = suggestion.recomendacao
        model.justificativa = suggestion.justificativa
        model.nivel_confianca = suggestion.nivel_confianca
        model.status = suggestion.status.value
        model.usuario_decisao_id = suggestion.usuario_decisao_id
        model.data_hora_decisao = suggestion.data_hora_decisao
        await self._session.flush()
