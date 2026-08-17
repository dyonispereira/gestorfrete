from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_suggestion_dto import AISuggestionDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_suggestion_repository import (
    SqlAlchemyAISuggestionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSuggestionsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    category: str | None
    target_entity_type: str | None
    target_entity_id: uuid.UUID | None
    status: str | None


@dataclass(frozen=True)
class ListSuggestionsResult:
    items: list[AISuggestionDTO]
    total: int


class ListSuggestionsHandler(QueryHandler[ListSuggestionsQuery, ListSuggestionsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSuggestionsQuery) -> ListSuggestionsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAISuggestionRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, categoria=query.category,
                entidade_alvo_tipo=query.target_entity_type, entidade_alvo_id=query.target_entity_id,
                status=query.status,
            )
            return ListSuggestionsResult(items=[AISuggestionDTO.from_entity(s) for s in items], total=total)
