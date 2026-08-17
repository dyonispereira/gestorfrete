from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.fleet.application.dtos.vehicle_availability_dto import VehicleAvailabilityDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_availability_repository import (
    SqlAlchemyVehicleAvailabilityRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListVehicleAvailabilityQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None


@dataclass(frozen=True)
class ListVehicleAvailabilityResult:
    items: list[VehicleAvailabilityDTO]
    total: int


class ListVehicleAvailabilityHandler(QueryHandler[ListVehicleAvailabilityQuery, ListVehicleAvailabilityResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehicleAvailabilityQuery) -> ListVehicleAvailabilityResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleAvailabilityRepository(session)
            items, total = await repo.list_page(page=query.page, limit=query.limit, status=query.status)
        return ListVehicleAvailabilityResult(items=[VehicleAvailabilityDTO.from_entity(i) for i in items], total=total)
