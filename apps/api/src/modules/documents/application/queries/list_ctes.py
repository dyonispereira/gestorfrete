from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListCtesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    trip_id: uuid.UUID | None = None
    status: str | None = None
    series: str | None = None
    access_key: str | None = None


@dataclass(frozen=True)
class ListCtesResult:
    items: list[CteDTO]
    total: int


class ListCtesHandler(QueryHandler[ListCtesQuery, ListCtesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListCtesQuery) -> ListCtesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyCteRepository(session)
            ctes, total = await repo.list_page(
                page=query.page, limit=query.limit, viagem_id=query.trip_id, status=query.status,
                serie=query.series, chave_acesso=query.access_key,
            )
        return ListCtesResult(items=[CteDTO.from_entity(c) for c in ctes], total=total)
