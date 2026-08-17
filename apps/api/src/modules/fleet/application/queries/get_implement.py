from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.implement_dto import ImplementDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetImplementQuery(Query):
    actor: AuthenticatedActor
    implement_id: uuid.UUID


class GetImplementHandler(QueryHandler[GetImplementQuery, ImplementDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetImplementQuery) -> ImplementDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyImplementRepository(session)
            implement = await repo.get_by_id(query.implement_id)
        if implement is None:
            raise NotFoundError("FLEET_IMPLEMENT_NOT_FOUND", "Implemento não encontrado.")
        return ImplementDTO.from_entity(implement)
