from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_technical_sheet_dto import VehicleTechnicalSheetDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_technical_sheet_repository import (
    SqlAlchemyVehicleTechnicalSheetRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetVehicleTechnicalSheetQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID


class GetVehicleTechnicalSheetHandler(QueryHandler[GetVehicleTechnicalSheetQuery, VehicleTechnicalSheetDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleTechnicalSheetQuery) -> VehicleTechnicalSheetDTO:
        async with self._session_factory() as session:
            vehicle_repo = SqlAlchemyVehicleRepository(session)
            vehicle = await vehicle_repo.get_by_id(query.vehicle_id)
            if vehicle is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            sheet_repo = SqlAlchemyVehicleTechnicalSheetRepository(session)
            sheet = await sheet_repo.get_by_vehicle_id(query.vehicle_id)
            if sheet is None:
                raise NotFoundError(
                    "FLEET_VEHICLE_TECHNICAL_SHEET_NOT_FOUND", "Veículo ainda não tem Ficha Técnica cadastrada."
                )

        return VehicleTechnicalSheetDTO.from_entity_and_vehicle(
            sheet,
            manufacturer=vehicle.fabricante,
            model=vehicle.modelo,
            manufacture_year=vehicle.ano_fabricacao,
            category_id=vehicle.categoria_veiculo_id,
        )
