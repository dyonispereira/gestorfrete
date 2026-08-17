from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTripsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status_operacional: str | None = None
    status_fiscal: str | None = None
    status_financeiro: str | None = None
    motorista_id: uuid.UUID | None = None
    veiculo_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    data_programada: date | None = None
    codigo: str | None = None


@dataclass(frozen=True)
class ListTripsResult:
    items: list[TripDTO]
    total: int


class ListTripsHandler(QueryHandler[ListTripsQuery, ListTripsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTripsQuery) -> ListTripsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyTripRepository(session)
            trips, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                status_operacional=query.status_operacional,
                status_fiscal=query.status_fiscal,
                status_financeiro=query.status_financeiro,
                motorista_id=query.motorista_id,
                veiculo_id=query.veiculo_id,
                cliente_id=query.cliente_id,
                data_programada=query.data_programada,
                codigo=query.codigo,
            )
        return ListTripsResult(items=[TripDTO.from_entity(t) for t in trips], total=total)
