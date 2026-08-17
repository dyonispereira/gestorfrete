from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO
from modules.freight.application.queries.list_occurrences import ListOccurrencesHandler, ListOccurrencesQuery
from modules.mobile.application.queries.ownership import assert_owns_trip
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOwnOccurrencesQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    trip_id: uuid.UUID
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ListOwnOccurrencesResult:
    items: list[OccurrenceDTO]
    total: int


class ListOwnOccurrencesHandler(QueryHandler[ListOwnOccurrencesQuery, ListOwnOccurrencesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOwnOccurrencesQuery) -> ListOwnOccurrencesResult:
        await assert_owns_trip(
            self._session_factory, actor=query.actor, driver_id=query.driver_id, trip_id=query.trip_id
        )
        result = await ListOccurrencesHandler(self._session_factory).handle(
            ListOccurrencesQuery(actor=query.actor, trip_id=query.trip_id, page=query.page, limit=query.limit)
        )
        return ListOwnOccurrencesResult(items=result.items, total=result.total)
