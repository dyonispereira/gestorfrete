from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_model_dto import AIModelDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAIModelsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    type: str | None
    logical_provider: str | None
    status: str | None


@dataclass(frozen=True)
class ListAIModelsResult:
    items: list[AIModelDTO]
    total: int


class ListAIModelsHandler(QueryHandler[ListAIModelsQuery, ListAIModelsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAIModelsQuery) -> ListAIModelsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIModelRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, tipo=query.type,
                fornecedor_logico=query.logical_provider, status=query.status,
            )
            return ListAIModelsResult(items=[AIModelDTO.from_entity(m) for m in items], total=total)
