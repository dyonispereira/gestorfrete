from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_suggestion_dto import AISuggestionDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_suggestion_repository import (
    SqlAlchemyAISuggestionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSuggestionQuery(Query):
    actor: AuthenticatedActor
    suggestion_id: uuid.UUID


class GetSuggestionHandler(QueryHandler[GetSuggestionQuery, AISuggestionDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSuggestionQuery) -> AISuggestionDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAISuggestionRepository(session)
            suggestion = await repo.get_by_id(query.suggestion_id)
        if suggestion is None:
            raise NotFoundError("AI_SUGGESTION_NOT_FOUND", "Sugestão de IA não encontrada.")
        return AISuggestionDTO.from_entity(suggestion)
