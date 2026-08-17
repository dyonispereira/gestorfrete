from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.fleet.application.dtos.vehicle_dto import VehicleDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListVehiclesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None
    placa: str | None = None
    status: str | None = None
    categoria_id: uuid.UUID | None = None
    fabricante: str | None = None
    modelo: str | None = None
    ano: int | None = None


@dataclass(frozen=True)
class ListVehiclesResult:
    items: list[VehicleDTO]
    total: int


class ListVehiclesHandler(QueryHandler[ListVehiclesQuery, ListVehiclesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehiclesQuery) -> ListVehiclesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleRepository(session)
            vehicles, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                search=query.search,
                placa=query.placa,
                status=query.status,
                categoria_id=query.categoria_id,
                fabricante=query.fabricante,
                modelo=query.modelo,
                ano=query.ano,
            )
        return ListVehiclesResult(items=[VehicleDTO.from_entity(v) for v in vehicles], total=total)
