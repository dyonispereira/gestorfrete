from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.trip_allocation_dto import TripAllocationDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_allocation_repository import (
    SqlAlchemyTripAllocationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTripAllocationsQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    history: bool = False


@dataclass(frozen=True)
class TripAllocationsResult:
    current: TripAllocationDTO | None
    items: list[TripAllocationDTO]


class GetTripAllocationsHandler(QueryHandler[GetTripAllocationsQuery, TripAllocationsResult]):
    """`GET /viagens/{id}/resources` — sem `?history=true`, devolve só a `VIGENTE`; com, a coleção
    completa (incluindo `SUBSTITUIDA`), `016-trip-resources.md`."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTripAllocationsQuery) -> TripAllocationsResult:
        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            if await trip_repo.get_by_id(query.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            allocation_repo = SqlAlchemyTripAllocationRepository(session)
            current = await allocation_repo.get_current_for_trip(query.trip_id)
            if current is None:
                raise NotFoundError("FREIGHT_TRIP_ALLOCATION_NOT_FOUND", "Viagem ainda não tem alocação.")

            items: list[TripAllocationDTO] = []
            if query.history:
                allocations = await allocation_repo.list_for_trip(query.trip_id, include_superseded=True)
                items = [TripAllocationDTO.from_entity(a) for a in allocations]

        return TripAllocationsResult(current=TripAllocationDTO.from_entity(current), items=items)
