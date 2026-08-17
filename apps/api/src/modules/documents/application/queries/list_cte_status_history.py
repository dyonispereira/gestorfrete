from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.documents.application.dtos.status_history_entry_dto import StatusHistoryEntryDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_status_history_repository import (
    SqlAlchemyCteStatusHistoryRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListCteStatusHistoryQuery(Query):
    actor: AuthenticatedActor
    cte_id: uuid.UUID
    cursor: str | None = None
    limit: int = 20
    status: str | None = None


@dataclass(frozen=True)
class ListCteStatusHistoryResult:
    items: list[StatusHistoryEntryDTO]
    next_cursor: str | None
    has_more: bool


class ListCteStatusHistoryHandler(QueryHandler[ListCteStatusHistoryQuery, ListCteStatusHistoryResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListCteStatusHistoryQuery) -> ListCteStatusHistoryResult:
        after_data_hora = None
        after_id = None
        if query.cursor is not None:
            try:
                after_data_hora, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("FISCAL_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            cte_repo = SqlAlchemyCteRepository(session)
            if await cte_repo.get_by_id(query.cte_id) is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            history_repo = SqlAlchemyCteStatusHistoryRepository(session)
            entries = await history_repo.list_page(
                query.cte_id, after_data_hora=after_data_hora, after_id=after_id, limit=query.limit + 1,
                status=query.status,
            )

        has_more = len(entries) > query.limit
        page = entries[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].data_hora, id=page[-1].id) if has_more and page else None
        return ListCteStatusHistoryResult(
            items=[StatusHistoryEntryDTO.from_entity(e) for e in page], next_cursor=next_cursor, has_more=has_more
        )
