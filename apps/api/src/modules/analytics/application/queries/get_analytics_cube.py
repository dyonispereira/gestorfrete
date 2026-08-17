from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.analytics_cube_dto import AnalyticsCubeDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_cube_repository import (
    SqlAlchemyAnalyticsCubeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAnalyticsCubeQuery(Query):
    actor: AuthenticatedActor
    cube_id: uuid.UUID


class GetAnalyticsCubeHandler(QueryHandler[GetAnalyticsCubeQuery, AnalyticsCubeDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAnalyticsCubeQuery) -> AnalyticsCubeDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAnalyticsCubeRepository(session)
            cube = await repo.get_by_id(query.cube_id)
        if cube is None:
            raise NotFoundError("ANALYTICS_CUBE_NOT_FOUND", "Cubo Analítico não encontrado.")
        return AnalyticsCubeDTO.from_entity(cube)
