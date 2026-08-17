from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.computer_vision_reading_dto import ComputerVisionReadingDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_computer_vision_reading_repository import (
    SqlAlchemyComputerVisionReadingRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListComputerVisionReadingsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    reading_type: str | None
    status: str | None
    human_review_required: bool | None


@dataclass(frozen=True)
class ListComputerVisionReadingsResult:
    items: list[ComputerVisionReadingDTO]
    total: int


class ListComputerVisionReadingsHandler(
    QueryHandler[ListComputerVisionReadingsQuery, ListComputerVisionReadingsResult]
):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListComputerVisionReadingsQuery) -> ListComputerVisionReadingsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyComputerVisionReadingRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, tipo_leitura=query.reading_type, status=query.status,
                revisao_humana_necessaria=query.human_review_required,
            )
            return ListComputerVisionReadingsResult(
                items=[ComputerVisionReadingDTO.from_entity(r) for r in items], total=total
            )
