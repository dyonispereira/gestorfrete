from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.fleet.application.dtos.vehicle_composition_dto import VehicleCompositionDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_composition_repository import (
    SqlAlchemyVehicleCompositionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListVehicleCompositionsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    veiculo_tracionador_id: uuid.UUID | None = None
    tipo_combinacao: str | None = None
    vigente: bool = True


@dataclass(frozen=True)
class ListVehicleCompositionsResult:
    items: list[VehicleCompositionDTO]
    total: int


class ListVehicleCompositionsHandler(QueryHandler[ListVehicleCompositionsQuery, ListVehicleCompositionsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehicleCompositionsQuery) -> ListVehicleCompositionsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyVehicleCompositionRepository(session)
            compositions, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                veiculo_tracionador_id=query.veiculo_tracionador_id,
                tipo_combinacao=query.tipo_combinacao,
                vigente=query.vigente,
            )
        return ListVehicleCompositionsResult(items=[VehicleCompositionDTO.from_entity(c) for c in compositions], total=total)
