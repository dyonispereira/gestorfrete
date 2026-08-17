from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_inference_dto import AIInferenceDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_inference_repository import (
    SqlAlchemyAIInferenceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

VIEW_COST_PERMISSION = "ai.inference.view_cost"


@dataclass(frozen=True)
class GetInferenceQuery(Query):
    actor: AuthenticatedActor
    inference_id: uuid.UUID
    held_permissions: frozenset[str]


class GetInferenceHandler(QueryHandler[GetInferenceQuery, AIInferenceDTO]):
    """Auditoria 7 — `cost` só é exposto com `ai.inference.view_cost` (D267-style), mesmo padrão de
    `GetTripFinancialsHandler` (Lote 6/7) e `ConsolidatedIndicatorResponse` (Lote 11)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetInferenceQuery) -> AIInferenceDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIInferenceRepository(session)
            inference = await repo.get_by_id(query.inference_id)
        if inference is None:
            raise NotFoundError("AI_INFERENCE_NOT_FOUND", "Inferência de IA não encontrada.")
        has_cost = VIEW_COST_PERMISSION in query.held_permissions
        return AIInferenceDTO.from_entity(inference, has_cost_permission=has_cost)
