from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.consolidated_indicator_dto import ConsolidatedIndicatorDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_consolidated_indicator_repository import (
    SqlAlchemyConsolidatedIndicatorRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetConsolidatedIndicatorQuery(Query):
    actor: AuthenticatedActor
    indicator_id: uuid.UUID


class GetConsolidatedIndicatorHandler(QueryHandler[GetConsolidatedIndicatorQuery, ConsolidatedIndicatorDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetConsolidatedIndicatorQuery) -> ConsolidatedIndicatorDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyConsolidatedIndicatorRepository(session)
            indicator = await repo.get_by_id(query.indicator_id)
        if indicator is None:
            raise NotFoundError("ANALYTICS_INDICATOR_NOT_FOUND", "Indicador Consolidado não encontrado.")
        return ConsolidatedIndicatorDTO.from_entity(indicator)
