from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_occurrence_repository import (
    SqlAlchemyOccurrenceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetOccurrenceQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    occurrence_id: uuid.UUID


class GetOccurrenceHandler(QueryHandler[GetOccurrenceQuery, OccurrenceDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetOccurrenceQuery) -> OccurrenceDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyOccurrenceRepository(session)
            occurrence = await repo.get_by_id(query.occurrence_id)
            if occurrence is None or occurrence.viagem_id != query.trip_id:
                raise NotFoundError("FREIGHT_OCCURRENCE_NOT_FOUND", "Ocorrência não encontrada.")
        return OccurrenceDTO.from_entity(occurrence)
