from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_dto import ClientDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetClientQuery(Query):
    actor: AuthenticatedActor
    client_id: uuid.UUID


class GetClientHandler(QueryHandler[GetClientQuery, ClientDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetClientQuery) -> ClientDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyClientRepository(session)
            client = await repo.get_by_id(query.client_id)
        if client is None:
            raise NotFoundError("CRM_CLIENT_NOT_FOUND", "Cliente não encontrado.")
        return ClientDTO.from_entity(client)
