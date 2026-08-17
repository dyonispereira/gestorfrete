from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.referenced_nfe_dto import ReferencedNfeDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_referenced_nfe_repository import (
    SqlAlchemyReferencedNfeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListReferencedNfesQuery(Query):
    actor: AuthenticatedActor
    cte_id: uuid.UUID


class ListReferencedNfesHandler(QueryHandler[ListReferencedNfesQuery, list[ReferencedNfeDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListReferencedNfesQuery) -> list[ReferencedNfeDTO]:
        async with self._session_factory() as session:
            cte_repo = SqlAlchemyCteRepository(session)
            if await cte_repo.get_by_id(query.cte_id) is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            nfe_repo = SqlAlchemyReferencedNfeRepository(session)
            nfes = await nfe_repo.list_for_cte(query.cte_id)
        return [ReferencedNfeDTO.from_entity(nfe) for nfe in nfes]
