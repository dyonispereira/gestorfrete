from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.metric_dto import MetricDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetMetricQuery(Query):
    actor: AuthenticatedActor
    metric_id: uuid.UUID


class GetMetricHandler(QueryHandler[GetMetricQuery, MetricDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetMetricQuery) -> MetricDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyMetricRepository(session)
            metric = await repo.get_by_id(query.metric_id)
        if metric is None:
            raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica não encontrada.")
        return MetricDTO.from_entity(metric)
