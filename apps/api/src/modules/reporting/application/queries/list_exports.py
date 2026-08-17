from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.reporting.application.dtos.export_dto import ExportDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_export_repository import (
    SqlAlchemyExportRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListExportsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    status: str | None
    saved_report_id: uuid.UUID | None


@dataclass(frozen=True)
class ListExportsResult:
    items: list[ExportDTO]
    total: int


class ListExportsHandler(QueryHandler[ListExportsQuery, ListExportsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListExportsQuery) -> ListExportsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyExportRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, saved_report_id=query.saved_report_id,
                usuario_id=query.actor.user_id,
            )
            return ListExportsResult(items=[ExportDTO.from_entity(e) for e in items], total=total)
