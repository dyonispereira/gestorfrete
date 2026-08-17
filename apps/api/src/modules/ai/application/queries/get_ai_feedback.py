from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_feedback_dto import AIFeedbackDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_feedback_repository import (
    SqlAlchemyAIFeedbackRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAIFeedbackQuery(Query):
    actor: AuthenticatedActor
    feedback_id: uuid.UUID


class GetAIFeedbackHandler(QueryHandler[GetAIFeedbackQuery, AIFeedbackDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAIFeedbackQuery) -> AIFeedbackDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIFeedbackRepository(session)
            feedback = await repo.get_by_id(query.feedback_id)
        if feedback is None:
            raise NotFoundError("AI_FEEDBACK_NOT_FOUND", "Feedback de IA não encontrado.")
        return AIFeedbackDTO.from_entity(feedback)
