from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_category_dto import VehicleCategoryDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetVehicleCategoryQuery(Query):
    actor: AuthenticatedActor
    vehicle_category_id: uuid.UUID


class GetVehicleCategoryHandler(QueryHandler[GetVehicleCategoryQuery, VehicleCategoryDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleCategoryQuery) -> VehicleCategoryDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleCategoryRepository(session)
            category = await repo.get_by_id(query.vehicle_category_id)
        if category is None:
            raise NotFoundError("FLEET_VEHICLE_CATEGORY_NOT_FOUND", "Categoria de Veículo não encontrada.")
        return VehicleCategoryDTO.from_entity(category)
