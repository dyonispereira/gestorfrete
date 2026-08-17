from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from shared.collaboration.domain.entities.comment import Comment
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_comment_repository import (
    SqlAlchemyCommentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTripCommentsQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    visible_to_client: bool | None


class ListTripCommentsHandler(QueryHandler[ListTripCommentsQuery, list[Comment]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTripCommentsQuery) -> list[Comment]:
        await GetTripHandler(self._session_factory).handle(GetTripQuery(actor=query.actor, trip_id=query.trip_id))
        async with self._session_factory() as session:
            repo = SqlAlchemyCommentRepository(session)
            comments = await repo.list_for_entity("VIAGEM", query.trip_id)
            if query.visible_to_client is not None:
                comments = [c for c in comments if c.visivel_cliente == query.visible_to_client]
            return comments
