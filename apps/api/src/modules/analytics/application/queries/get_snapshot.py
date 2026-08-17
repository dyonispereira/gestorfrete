from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.analytical_snapshot_dto import AnalyticalSnapshotDTO, ParticipatingMetricDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytical_snapshot_repository import (
    SqlAlchemyAnalyticalSnapshotRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSnapshotQuery(Query):
    actor: AuthenticatedActor
    snapshot_id: uuid.UUID


class GetSnapshotHandler(QueryHandler[GetSnapshotQuery, AnalyticalSnapshotDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSnapshotQuery) -> AnalyticalSnapshotDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAnalyticalSnapshotRepository(session)
            snapshot = await repo.get_by_id(query.snapshot_id)
            if snapshot is None:
                raise NotFoundError("ANALYTICS_SNAPSHOT_NOT_FOUND", "Snapshot não encontrado.")
            indicator_ids = await repo.list_indicator_ids(query.snapshot_id)
            participants = await repo.get_participating_metrics(query.snapshot_id)

        return AnalyticalSnapshotDTO.from_entity(
            snapshot,
            participating_metrics=[ParticipatingMetricDTO(metric_id=mid, metric_version=v) for mid, v in participants],
            indicator_ids=indicator_ids,
        )
