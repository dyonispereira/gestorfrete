from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.reporting.application.dtos.dashboard_dto import DashboardDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_dashboard_repository import (
    SqlAlchemyDashboardRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListDashboardsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    search: str | None
    status: str | None
    include_shared: bool


@dataclass(frozen=True)
class ListDashboardsResult:
    items: list[DashboardDTO]
    total: int


class ListDashboardsHandler(QueryHandler[ListDashboardsQuery, ListDashboardsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListDashboardsQuery) -> ListDashboardsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyDashboardRepository(session)
            items, total = await repo.list_own_and_shared(
                page=query.page, limit=query.limit, search=query.search, status=query.status,
                usuario_id=query.actor.user_id, include_shared=query.include_shared,
            )
            return ListDashboardsResult(items=[DashboardDTO.from_entity(d) for d in items], total=total)
