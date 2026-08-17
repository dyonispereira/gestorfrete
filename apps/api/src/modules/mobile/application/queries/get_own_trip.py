from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetOwnTripQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    trip_id: uuid.UUID


class GetOwnTripHandler(QueryHandler[GetOwnTripQuery, TripDTO]):
    """`055-driver-trips.md` — `403`, nunca `404`, quando a Viagem existe mas não pertence ao
    Motorista da sessão (enumeration-safety: nunca revela se a Viagem existe para outro Motorista)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetOwnTripQuery) -> TripDTO:
        dto = await GetTripHandler(self._session_factory).handle(GetTripQuery(actor=query.actor, trip_id=query.trip_id))
        if dto.motorista_id != query.driver_id:
            raise AuthorizationError("FREIGHT_TRIP_FORBIDDEN", "Viagem não pertence ao Motorista da sessão.")
        return dto
