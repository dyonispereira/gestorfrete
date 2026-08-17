from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_occurrence_repository import (
    SqlAlchemyOccurrenceRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOccurrencesQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    page: int = 1
    limit: int = 20
    tipo: str | None = None
    status: str | None = None
    gravidade: str | None = None


@dataclass(frozen=True)
class ListOccurrencesResult:
    items: list[OccurrenceDTO]
    total: int


class ListOccurrencesHandler(QueryHandler[ListOccurrencesQuery, ListOccurrencesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOccurrencesQuery) -> ListOccurrencesResult:
        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            if await trip_repo.get_by_id(query.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            occurrence_repo = SqlAlchemyOccurrenceRepository(session)
            occurrences, total = await occurrence_repo.list_page_for_trip(
                query.trip_id, page=query.page, limit=query.limit, tipo=query.tipo, status=query.status, gravidade=query.gravidade
            )
        return ListOccurrencesResult(items=[OccurrenceDTO.from_entity(o) for o in occurrences], total=total)
