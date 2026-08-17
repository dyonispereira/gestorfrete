from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.storage.application.dtos.file_dto import FileDTO
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetFileQuery(Query):
    actor: AuthenticatedActor
    file_id: uuid.UUID


class GetFileHandler(QueryHandler[GetFileQuery, FileDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetFileQuery) -> FileDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyFileRepository(session)
            file = await repo.get_by_id(query.file_id)
            if file is None:
                raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")
            return FileDTO.from_entity(file)
