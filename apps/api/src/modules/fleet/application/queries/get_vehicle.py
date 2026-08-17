from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_dto import VehicleDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetVehicleQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID


class GetVehicleHandler(QueryHandler[GetVehicleQuery, VehicleDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleQuery) -> VehicleDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleRepository(session)
            vehicle = await repo.get_by_id(query.vehicle_id)
        if vehicle is None:
            raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")
        return VehicleDTO.from_entity(vehicle)
