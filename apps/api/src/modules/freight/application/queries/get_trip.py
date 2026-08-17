from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTripQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class GetTripHandler(QueryHandler[GetTripQuery, TripDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTripQuery) -> TripDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTripRepository(session)
            trip = await repo.get_by_id(query.trip_id)
        if trip is None:
            raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
        return TripDTO.from_entity(trip)
