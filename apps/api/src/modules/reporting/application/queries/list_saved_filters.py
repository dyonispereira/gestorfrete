from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.reporting.application.dtos.saved_filter_dto import SavedFilterDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_filter_repository import (
    SqlAlchemySavedFilterRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSavedFiltersQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    search: str | None
    status: str | None


@dataclass(frozen=True)
class ListSavedFiltersResult:
    items: list[SavedFilterDTO]
    total: int


class ListSavedFiltersHandler(QueryHandler[ListSavedFiltersQuery, ListSavedFiltersResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSavedFiltersQuery) -> ListSavedFiltersResult:
        async with self._session_factory() as session:
            repo = SqlAlchemySavedFilterRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, status=query.status,
                usuario_id=query.actor.user_id,
            )
            return ListSavedFiltersResult(items=[SavedFilterDTO.from_entity(f) for f in items], total=total)
