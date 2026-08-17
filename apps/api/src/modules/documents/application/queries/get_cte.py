from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetCteQuery(Query):
    actor: AuthenticatedActor
    cte_id: uuid.UUID


class GetCteHandler(QueryHandler[GetCteQuery, CteDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetCteQuery) -> CteDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyCteRepository(session)
            cte = await repo.get_by_id(query.cte_id)
        if cte is None:
            raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")
        return CteDTO.from_entity(cte)
