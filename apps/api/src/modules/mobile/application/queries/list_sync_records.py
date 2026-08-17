from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.mobile.application.dtos.sync_dto import SyncRecordDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_sync_record_repository import (
    SqlAlchemySyncRecordRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSyncRecordsQuery(Query):
    actor: AuthenticatedActor
    session_id: uuid.UUID
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ListSyncRecordsResult:
    items: list[SyncRecordDTO]
    total: int


class ListSyncRecordsHandler(QueryHandler[ListSyncRecordsQuery, ListSyncRecordsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSyncRecordsQuery) -> ListSyncRecordsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemySyncRecordRepository(session)
            items, total = await repo.list_page(sessao_mobile_id=query.session_id, page=query.page, limit=query.limit)
        return ListSyncRecordsResult(
            items=[
                SyncRecordDTO.from_entity(
                    r, duracao_ms=int((r.data_hora_fim - r.data_hora_inicio).total_seconds() * 1000)
                )
                for r in items
            ],
            total=total,
        )
