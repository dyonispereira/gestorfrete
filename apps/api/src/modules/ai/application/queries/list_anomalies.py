from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_anomaly_dto import AIAnomalyDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_anomaly_repository import (
    SqlAlchemyAIAnomalyRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAnomaliesQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    source_reading_type: str | None
    status: str | None


@dataclass(frozen=True)
class ListAnomaliesResult:
    items: list[AIAnomalyDTO]
    total: int


class ListAnomaliesHandler(QueryHandler[ListAnomaliesQuery, ListAnomaliesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAnomaliesQuery) -> ListAnomaliesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIAnomalyRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, leitura_origem_tipo=query.source_reading_type,
                status=query.status,
            )
            return ListAnomaliesResult(items=[AIAnomalyDTO.from_entity(a) for a in items], total=total)
