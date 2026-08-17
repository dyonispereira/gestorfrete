from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.fleet.application.dtos.implement_dto import ImplementDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListImplementsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None
    tipo_carroceria: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListImplementsResult:
    items: list[ImplementDTO]
    total: int


class ListImplementsHandler(QueryHandler[ListImplementsQuery, ListImplementsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListImplementsQuery) -> ListImplementsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyImplementRepository(session)
            implements, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, tipo_carroceria=query.tipo_carroceria, status=query.status
            )
        return ListImplementsResult(items=[ImplementDTO.from_entity(i) for i in implements], total=total)
