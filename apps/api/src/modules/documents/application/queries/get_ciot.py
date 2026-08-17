from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.ciot_dto import CiotDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_repository import (
    SqlAlchemyCiotRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetCiotQuery(Query):
    actor: AuthenticatedActor
    ciot_id: uuid.UUID


class GetCiotHandler(QueryHandler[GetCiotQuery, CiotDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetCiotQuery) -> CiotDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyCiotRepository(session)
            ciot = await repo.get_by_id(query.ciot_id)
        if ciot is None:
            raise NotFoundError("FISCAL_CIOT_NOT_FOUND", "CIOT não encontrado.")
        return CiotDTO.from_entity(ciot)
