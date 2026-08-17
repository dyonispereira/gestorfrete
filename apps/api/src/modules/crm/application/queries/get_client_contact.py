from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_contact_dto import ClientContactDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_contact_repository import (
    SqlAlchemyClientContactRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetClientContactQuery(Query):
    actor: AuthenticatedActor
    client_id: uuid.UUID
    contact_id: uuid.UUID


class GetClientContactHandler(QueryHandler[GetClientContactQuery, ClientContactDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetClientContactQuery) -> ClientContactDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyClientContactRepository(session)
            contact = await repo.get_by_id(query.contact_id)
        if contact is None or contact.cliente_id != query.client_id:
            raise NotFoundError("CRM_CLIENT_CONTACT_NOT_FOUND", "Contato não encontrado.")
        return ClientContactDTO.from_entity(contact)
