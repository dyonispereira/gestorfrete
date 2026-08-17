from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.storage.infrastructure.object_storage import DOWNLOAD_URL_EXPIRY, presigned_download_url
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetFileDownloadUrlQuery(Query):
    actor: AuthenticatedActor
    file_id: uuid.UUID


@dataclass(frozen=True)
class DownloadUrlResult:
    download_url: str
    expires_at: datetime


class GetFileDownloadUrlHandler(QueryHandler[GetFileDownloadUrlQuery, DownloadUrlResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetFileDownloadUrlQuery) -> DownloadUrlResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyFileRepository(session)
            file = await repo.get_by_id(query.file_id)
            if file is None:
                raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")

        download_url = await presigned_download_url(file.storage_key)
        return DownloadUrlResult(download_url=download_url, expires_at=datetime.now(timezone.utc) + DOWNLOAD_URL_EXPIRY)
