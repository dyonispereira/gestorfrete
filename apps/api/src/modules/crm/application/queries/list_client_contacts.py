from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_contact_dto import ClientContactDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_contact_repository import (
    SqlAlchemyClientContactRepository,
)
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListClientContactsQuery(Query):
    actor: AuthenticatedActor
    client_id: uuid.UUID


class ListClientContactsHandler(QueryHandler[ListClientContactsQuery, list[ClientContactDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListClientContactsQuery) -> list[ClientContactDTO]:
        async with self._session_factory() as session:
            client_repo = SqlAlchemyClientRepository(session)
            if await client_repo.get_by_id(query.client_id) is None:
                raise NotFoundError("CRM_CLIENT_NOT_FOUND", "Cliente não encontrado.")

            contact_repo = SqlAlchemyClientContactRepository(session)
            contacts = await contact_repo.list_for_client(query.client_id)
        return [ClientContactDTO.from_entity(c) for c in contacts]
