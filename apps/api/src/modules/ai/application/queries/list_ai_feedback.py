from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_feedback_dto import AIFeedbackDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_feedback_repository import (
    SqlAlchemyAIFeedbackRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAIFeedbackQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    output_type: str | None
    output_id: uuid.UUID | None
    result: str | None


@dataclass(frozen=True)
class ListAIFeedbackResult:
    items: list[AIFeedbackDTO]
    total: int


class ListAIFeedbackHandler(QueryHandler[ListAIFeedbackQuery, ListAIFeedbackResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAIFeedbackQuery) -> ListAIFeedbackResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIFeedbackRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, saida_ia_tipo=query.output_type,
                saida_ia_id=query.output_id, resultado=query.result,
            )
            return ListAIFeedbackResult(items=[AIFeedbackDTO.from_entity(f) for f in items], total=total)
