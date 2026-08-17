from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.referenced_nfe_dto import ReferencedNfeDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_referenced_nfe_repository import (
    SqlAlchemyReferencedNfeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetReferencedNfeQuery(Query):
    actor: AuthenticatedActor
    referenced_nfe_id: uuid.UUID


class GetReferencedNfeHandler(QueryHandler[GetReferencedNfeQuery, ReferencedNfeDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetReferencedNfeQuery) -> ReferencedNfeDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyReferencedNfeRepository(session)
            nfe = await repo.get_by_id(query.referenced_nfe_id)
        if nfe is None:
            raise NotFoundError("FISCAL_NFE_REFERENCE_NOT_FOUND", "NF-e Referenciada não encontrada.")
        return ReferencedNfeDTO.from_entity(nfe)
