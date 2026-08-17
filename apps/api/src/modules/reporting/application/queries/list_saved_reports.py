from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.reporting.application.dtos.saved_report_dto import SavedReportDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSavedReportsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    search: str | None
    output_format: str | None
    status: str | None


@dataclass(frozen=True)
class ListSavedReportsResult:
    items: list[SavedReportDTO]
    total: int


class ListSavedReportsHandler(QueryHandler[ListSavedReportsQuery, ListSavedReportsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSavedReportsQuery) -> ListSavedReportsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemySavedReportRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, output_format=query.output_format,
                status=query.status, usuario_id=query.actor.user_id,
            )
            return ListSavedReportsResult(items=[SavedReportDTO.from_entity(r) for r in items], total=total)
