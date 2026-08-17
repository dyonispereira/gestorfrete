from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_composition_dto import VehicleCompositionDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_composition_repository import (
    SqlAlchemyVehicleCompositionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetVehicleCompositionQuery(Query):
    actor: AuthenticatedActor
    composition_id: uuid.UUID


class GetVehicleCompositionHandler(QueryHandler[GetVehicleCompositionQuery, VehicleCompositionDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleCompositionQuery) -> VehicleCompositionDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleCompositionRepository(session)
            composition = await repo.get_by_id(query.composition_id)
        if composition is None:
            raise NotFoundError("FLEET_COMPOSITION_NOT_FOUND", "Composição Veicular não encontrada.")
        return VehicleCompositionDTO.from_entity(composition)
