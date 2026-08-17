from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.application.queries.list_trips import ListTripsHandler, ListTripsQuery
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOwnTripsQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    page: int = 1
    limit: int = 20
    status_operacional: str | None = None


@dataclass(frozen=True)
class ListOwnTripsResult:
    items: list[TripDTO]
    total: int


class ListOwnTripsHandler(QueryHandler[ListOwnTripsQuery, ListOwnTripsResult]):
    """`055-driver-trips.md` — D295: `motorista_id` nunca vem do cliente, sempre forçado a partir
    da Sessão. Reaproveita `ListTripsHandler` (`freight`) sem alteração, D303."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOwnTripsQuery) -> ListOwnTripsResult:
        result = await ListTripsHandler(self._session_factory).handle(
            ListTripsQuery(
                actor=query.actor, page=query.page, limit=query.limit,
                status_operacional=query.status_operacional, motorista_id=query.driver_id,
            )
        )
        return ListOwnTripsResult(items=result.items, total=result.total)
