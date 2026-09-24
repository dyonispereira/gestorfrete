from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.trip_allocation_dto import TripAllocationDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_allocation_repository import (
    SqlAlchemyTripAllocationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTripAllocationsQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    history: bool = False


@dataclass(frozen=True)
class TripAllocationsResult:
    current: TripAllocationDTO | None
    items: list[TripAllocationDTO]


class GetTripAllocationsHandler(QueryHandler[GetTripAllocationsQuery, TripAllocationsResult]):
    """`GET /viagens/{id}/resources` — sem `?history=true`, devolve só a `VIGENTE`; com, a coleção
    completa (incluindo `SUBSTITUIDA`/`ENCERRADA`), `016-trip-resources.md`.

    Reconciliado (V1 Operational Hardening, Parte 1): antes, `current is None` sempre levantava
    `FREIGHT_TRIP_ALLOCATION_NOT_FOUND`, mesmo com `?history=true` — inofensivo enquanto a
    Alocação `VIGENTE` nunca terminava (o bug que esta rodada corrige). Com `TripAllocation.end()`
    em uso, uma Viagem `FINALIZADA`/`CANCELADA` passa a ter zero `VIGENTE` legitimamente; sem essa
    ressalva, `?history=true` ficaria inacessível justamente para a Viagem cujo histórico faz mais
    sentido consultar. `history=false` continua exigindo uma `VIGENTE` (não há "corrente" a mostrar
    quando a Viagem já terminou ou nunca teve recursos)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTripAllocationsQuery) -> TripAllocationsResult:
        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            if await trip_repo.get_by_id(query.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            allocation_repo = SqlAlchemyTripAllocationRepository(session)
            current = await allocation_repo.get_current_for_trip(query.trip_id)

            if not query.history:
                if current is None:
                    raise NotFoundError("FREIGHT_TRIP_ALLOCATION_NOT_FOUND", "Viagem ainda não tem alocação vigente.")
                return TripAllocationsResult(current=TripAllocationDTO.from_entity(current), items=[])

            allocations = await allocation_repo.list_for_trip(query.trip_id, include_superseded=True)
            if not allocations:
                raise NotFoundError("FREIGHT_TRIP_ALLOCATION_NOT_FOUND", "Viagem ainda não tem alocação.")

        return TripAllocationsResult(
            current=TripAllocationDTO.from_entity(current) if current is not None else None,
            items=[TripAllocationDTO.from_entity(a) for a in allocations],
        )
