from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from shared.collaboration.domain.entities.attachment import Attachment
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTripAttachmentsQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class ListTripAttachmentsHandler(QueryHandler[ListTripAttachmentsQuery, list[Attachment]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTripAttachmentsQuery) -> list[Attachment]:
        await GetTripHandler(self._session_factory).handle(GetTripQuery(actor=query.actor, trip_id=query.trip_id))
        async with self._session_factory() as session:
            repo = SqlAlchemyAttachmentRepository(session)
            return await repo.list_for_entity("VIAGEM", query.trip_id)
