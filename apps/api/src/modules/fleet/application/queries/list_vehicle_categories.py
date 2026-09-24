from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.fleet.application.dtos.vehicle_category_dto import VehicleCategoryDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListVehicleCategoriesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class ListVehicleCategoriesResult:
    items: list[VehicleCategoryDTO]
    total: int


class ListVehicleCategoriesHandler(QueryHandler[ListVehicleCategoriesQuery, ListVehicleCategoriesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehicleCategoriesQuery) -> ListVehicleCategoriesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleCategoryRepository(session)
            categories, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, search=query.search
            )
        return ListVehicleCategoriesResult(items=[VehicleCategoryDTO.from_entity(c) for c in categories], total=total)
