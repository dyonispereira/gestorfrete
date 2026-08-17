from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.reporting.application.dtos.scheduled_update_dto import ScheduledUpdateDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_scheduled_update_repository import (
    SqlAlchemyScheduledUpdateRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListScheduledUpdatesQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    metric_id: uuid.UUID | None
    cube_id: uuid.UUID | None
    mode: str | None
    status: str | None


@dataclass(frozen=True)
class ListScheduledUpdatesResult:
    items: list[ScheduledUpdateDTO]
    total: int


class ListScheduledUpdatesHandler(QueryHandler[ListScheduledUpdatesQuery, ListScheduledUpdatesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListScheduledUpdatesQuery) -> ListScheduledUpdatesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyScheduledUpdateRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, metric_id=query.metric_id, cube_id=query.cube_id,
                mode=query.mode, status=query.status,
            )
            return ListScheduledUpdatesResult(items=[ScheduledUpdateDTO.from_entity(s) for s in items], total=total)
