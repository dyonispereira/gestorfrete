from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.metric_dto import MetricDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListMetricsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    search: str | None
    temporal_granularity: str | None
    dimensional_granularity: str | None
    status: str | None


@dataclass(frozen=True)
class ListMetricsResult:
    items: list[MetricDTO]
    total: int


class ListMetricsHandler(QueryHandler[ListMetricsQuery, ListMetricsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListMetricsQuery) -> ListMetricsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyMetricRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search,
                temporal_granularity=query.temporal_granularity,
                dimensional_granularity=query.dimensional_granularity, status=query.status,
            )
            return ListMetricsResult(items=[MetricDTO.from_entity(m) for m in items], total=total)
