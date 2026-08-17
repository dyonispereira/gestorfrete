from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import ValidationError
from modules.documents.application.dtos.fiscal_event_dto import FiscalEventDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_event_repository import (
    SqlAlchemyFiscalEventRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListFiscalEventsQuery(Query):
    actor: AuthenticatedActor
    cursor: str | None = None
    limit: int = 20
    document_type: str | None = None
    document_id: uuid.UUID | None = None
    external_protocol: str | None = None
    started_at_from: datetime | None = None
    started_at_to: datetime | None = None
    result: str | None = None
    origin: str | None = None
    attempt_number: int | None = None


@dataclass(frozen=True)
class ListFiscalEventsResult:
    items: list[FiscalEventDTO]
    next_cursor: str | None
    has_more: bool


class ListFiscalEventsHandler(QueryHandler[ListFiscalEventsQuery, ListFiscalEventsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListFiscalEventsQuery) -> ListFiscalEventsResult:
        cursor_data_hora = None
        cursor_id = None
        if query.cursor is not None:
            try:
                cursor_data_hora, cursor_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("FISCAL_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            repo = SqlAlchemyFiscalEventRepository(session)
            events = await repo.list_page(
                cursor_data_hora=cursor_data_hora, cursor_id=cursor_id, limit=query.limit + 1,
                documento_tipo=query.document_type, documento_id=query.document_id,
                protocolo_externo=query.external_protocol, started_at_from=query.started_at_from,
                started_at_to=query.started_at_to, resultado=query.result, origem=query.origin,
                numero_tentativa=query.attempt_number,
            )

        has_more = len(events) > query.limit
        page = events[: query.limit]
        next_cursor = (
            encode_cursor(data_hora=page[-1].data_hora_inicio, id=page[-1].id) if has_more and page else None
        )
        return ListFiscalEventsResult(
            items=[FiscalEventDTO.from_entity(e) for e in page], next_cursor=next_cursor, has_more=has_more
        )
