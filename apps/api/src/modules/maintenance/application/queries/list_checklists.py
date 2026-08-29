from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListChecklistsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    referencia_tipo: str | None = None
    referencia_id: uuid.UUID | None = None
    tipo: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListChecklistsResult:
    items: list[ChecklistDTO]
    total: int


class ListChecklistsHandler(QueryHandler[ListChecklistsQuery, ListChecklistsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListChecklistsQuery) -> ListChecklistsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyChecklistRepository(session)
            checklists, total = await repo.list_page(
                page=query.page, limit=query.limit, referencia_tipo=query.referencia_tipo,
                referencia_id=query.referencia_id, tipo=query.tipo, status=query.status,
            )
        return ListChecklistsResult(items=[ChecklistDTO.from_entity(c) for c in checklists], total=total)
