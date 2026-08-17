from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.documents.application.dtos.ciot_dto import CiotDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_repository import (
    SqlAlchemyCiotRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListCiotsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    trip_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListCiotsResult:
    items: list[CiotDTO]
    total: int


class ListCiotsHandler(QueryHandler[ListCiotsQuery, ListCiotsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListCiotsQuery) -> ListCiotsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyCiotRepository(session)
            ciots, total = await repo.list_page(
                page=query.page, limit=query.limit, viagem_id=query.trip_id, motorista_id=query.driver_id,
                status=query.status,
            )
        return ListCiotsResult(items=[CiotDTO.from_entity(c) for c in ciots], total=total)
