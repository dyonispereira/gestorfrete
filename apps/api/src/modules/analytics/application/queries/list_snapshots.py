from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.analytical_snapshot_dto import AnalyticalSnapshotDTO, ParticipatingMetricDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytical_snapshot_repository import (
    SqlAlchemyAnalyticalSnapshotRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSnapshotsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    reference_period: str | None
    processing_origin: str | None
    status: str | None


@dataclass(frozen=True)
class ListSnapshotsResult:
    items: list[AnalyticalSnapshotDTO]
    total: int


class ListSnapshotsHandler(QueryHandler[ListSnapshotsQuery, ListSnapshotsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSnapshotsQuery) -> ListSnapshotsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAnalyticalSnapshotRepository(session)
            snapshots, total = await repo.list_page(
                page=query.page, limit=query.limit, reference_period=query.reference_period,
                processing_origin=query.processing_origin, status=query.status,
            )
            items = []
            for snapshot in snapshots:
                indicator_ids = await repo.list_indicator_ids(snapshot.id)
                participants = await repo.get_participating_metrics(snapshot.id)
                items.append(
                    AnalyticalSnapshotDTO.from_entity(
                        snapshot,
                        participating_metrics=[
                            ParticipatingMetricDTO(metric_id=mid, metric_version=v) for mid, v in participants
                        ],
                        indicator_ids=indicator_ids,
                    )
                )
            return ListSnapshotsResult(items=items, total=total)
