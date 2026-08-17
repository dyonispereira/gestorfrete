from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.computer_vision_reading_dto import ComputerVisionReadingDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_computer_vision_reading_repository import (
    SqlAlchemyComputerVisionReadingRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetComputerVisionReadingQuery(Query):
    actor: AuthenticatedActor
    reading_id: uuid.UUID


class GetComputerVisionReadingHandler(QueryHandler[GetComputerVisionReadingQuery, ComputerVisionReadingDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetComputerVisionReadingQuery) -> ComputerVisionReadingDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyComputerVisionReadingRepository(session)
            reading = await repo.get_by_id(query.reading_id)
        if reading is None:
            raise NotFoundError("AI_CV_READING_NOT_FOUND", "Leitura por Visão Computacional não encontrada.")
        return ComputerVisionReadingDTO.from_entity(reading)
