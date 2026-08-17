from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.mdfe_dto import MdfeDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetMdfeQuery(Query):
    actor: AuthenticatedActor
    mdfe_id: uuid.UUID


class GetMdfeHandler(QueryHandler[GetMdfeQuery, MdfeDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetMdfeQuery) -> MdfeDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyMdfeRepository(session)
            mdfe = await repo.get_by_id(query.mdfe_id)
            if mdfe is None:
                raise NotFoundError("FISCAL_MDFE_NOT_FOUND", "MDF-e não encontrado.")
            cte_ids = await repo.list_cte_ids(mdfe.id)
        return MdfeDTO.from_entity(mdfe, cte_ids=cte_ids)
