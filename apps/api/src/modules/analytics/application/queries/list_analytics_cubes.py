from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.analytics_cube_dto import AnalyticsCubeDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_cube_repository import (
    SqlAlchemyAnalyticsCubeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAnalyticsCubesQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    search: str | None
    status: str | None


@dataclass(frozen=True)
class ListAnalyticsCubesResult:
    items: list[AnalyticsCubeDTO]
    total: int


class ListAnalyticsCubesHandler(QueryHandler[ListAnalyticsCubesQuery, ListAnalyticsCubesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAnalyticsCubesQuery) -> ListAnalyticsCubesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAnalyticsCubeRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, status=query.status
            )
            return ListAnalyticsCubesResult(items=[AnalyticsCubeDTO.from_entity(c) for c in items], total=total)
