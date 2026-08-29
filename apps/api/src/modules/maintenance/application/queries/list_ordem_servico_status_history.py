from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.maintenance.application.dtos.ordem_servico_status_history_entry_dto import (
    OrdemServicoStatusHistoryEntryDTO,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOrdemServicoStatusHistoryQuery(Query):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID
    cursor: str | None = None
    limit: int = 20
    status: str | None = None


@dataclass(frozen=True)
class ListOrdemServicoStatusHistoryResult:
    items: list[OrdemServicoStatusHistoryEntryDTO]
    next_cursor: str | None
    has_more: bool


class ListOrdemServicoStatusHistoryHandler(
    QueryHandler[ListOrdemServicoStatusHistoryQuery, ListOrdemServicoStatusHistoryResult]
):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOrdemServicoStatusHistoryQuery) -> ListOrdemServicoStatusHistoryResult:
        after_data_hora = None
        after_id = None
        if query.cursor is not None:
            try:
                after_data_hora, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("MAINTENANCE_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            os_repo = SqlAlchemyOrdemServicoRepository(session)
            if await os_repo.get_by_id(query.ordem_servico_id) is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(session)
            entries = await history_repo.list_page(
                query.ordem_servico_id, after_data_hora=after_data_hora, after_id=after_id, limit=query.limit + 1,
                status=query.status,
            )

        has_more = len(entries) > query.limit
        page = entries[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].data_hora, id=page[-1].id) if has_more and page else None
        return ListOrdemServicoStatusHistoryResult(
            items=[OrdemServicoStatusHistoryEntryDTO.from_entity(e) for e in page], next_cursor=next_cursor,
            has_more=has_more,
        )
