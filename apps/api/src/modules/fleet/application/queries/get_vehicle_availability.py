from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_availability_dto import VehicleAvailabilityDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_availability_repository import (
    SqlAlchemyVehicleAvailabilityRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetVehicleAvailabilityQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID


class GetVehicleAvailabilityHandler(QueryHandler[GetVehicleAvailabilityQuery, VehicleAvailabilityDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleAvailabilityQuery) -> VehicleAvailabilityDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleAvailabilityRepository(session)
            availability = await repo.get_by_vehicle_id(query.vehicle_id)
        if availability is None:
            raise NotFoundError(
                "FLEET_VEHICLE_AVAILABILITY_NOT_FOUND",
                "Veículo existe, mas a projeção de disponibilidade ainda não foi materializada.",
            )
        return VehicleAvailabilityDTO.from_entity(availability)
