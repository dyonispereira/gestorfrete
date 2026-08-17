from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.storage.application.dtos.file_dto import FileDTO
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListFilesQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    mime_type: str | None
    origin: str | None
    status: str


@dataclass(frozen=True)
class ListFilesResult:
    items: list[FileDTO]
    total: int


class ListFilesHandler(QueryHandler[ListFilesQuery, ListFilesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListFilesQuery) -> ListFilesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyFileRepository(session)
            files, total = await repo.list_page(
                page=query.page, limit=query.limit, mime_type=query.mime_type, origin=query.origin,
                status=query.status,
            )
            return ListFilesResult(items=[FileDTO.from_entity(f) for f in files], total=total)
