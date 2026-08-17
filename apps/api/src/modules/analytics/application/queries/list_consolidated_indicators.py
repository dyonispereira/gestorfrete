from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.consolidated_indicator_dto import ConsolidatedIndicatorDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_consolidated_indicator_repository import (
    SqlAlchemyConsolidatedIndicatorRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListConsolidatedIndicatorsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    metric_id: uuid.UUID | None
    dimension_type: str | None
    dimension_id: uuid.UUID | None
    reference_period: str | None
    status: str | None


@dataclass(frozen=True)
class ListConsolidatedIndicatorsResult:
    items: list[ConsolidatedIndicatorDTO]
    total: int


class ListConsolidatedIndicatorsHandler(
    QueryHandler[ListConsolidatedIndicatorsQuery, ListConsolidatedIndicatorsResult]
):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListConsolidatedIndicatorsQuery) -> ListConsolidatedIndicatorsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyConsolidatedIndicatorRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, metric_id=query.metric_id,
                dimension_type=query.dimension_type, dimension_id=query.dimension_id,
                reference_period=query.reference_period, status=query.status,
            )
            return ListConsolidatedIndicatorsResult(
                items=[ConsolidatedIndicatorDTO.from_entity(i) for i in items], total=total
            )
