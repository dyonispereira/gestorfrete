from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.freight.application.dtos.trip_timeline_entry_dto import TripTimelineEntryDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_occurrence_repository import (
    SqlAlchemyOccurrenceRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_comment_repository import (
    SqlAlchemyCommentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_STATUS_HISTORY_SOURCE = {
    "OPERACIONAL": "STATUS_OPERACIONAL",
    "FISCAL": "STATUS_FISCAL",
    "FINANCEIRO": "STATUS_FINANCEIRO",
    "COMPOSTO": "STATUS_COMPOSTO",
}


def _encode_cursor(data_hora: datetime) -> str:
    return base64.urlsafe_b64encode(json.dumps({"data_hora": data_hora.isoformat()}).encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return datetime.fromisoformat(payload["data_hora"])
    except Exception as exc:
        raise ValidationError("FREIGHT_INVALID_CURSOR", "Cursor de paginação inválido.") from exc


@dataclass(frozen=True)
class ListTripTimelineQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    cursor: str | None = None
    limit: int = 50


@dataclass(frozen=True)
class ListTripTimelineResult:
    items: list[TripTimelineEntryDTO]
    next_cursor: str | None
    has_more: bool


class ListTripTimelineHandler(QueryHandler[ListTripTimelineQuery, ListTripTimelineResult]):
    """D372 — união de `viagem_status_history` + `ocorrencias` + (D416, Lote 10) `anexos`/
    `comentarios` da Viagem, cursor-paginada. Nenhum `Repository` de uma única tabela: monta a fusão
    na Application, exatamente como `019-trip-timeline.md`/`083-timelines.md` definem. Checklist/
    Abastecimento/OS/Documento Fiscal continuam de fora — nenhum tem endpoint de API ainda."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTripTimelineQuery) -> ListTripTimelineResult:
        after_data_hora = _decode_cursor(query.cursor) if query.cursor is not None else None

        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            if await trip_repo.get_by_id(query.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            history_repo = SqlAlchemyTripStatusHistoryRepository(session)
            occurrence_repo = SqlAlchemyOccurrenceRepository(session)
            attachment_repo = SqlAlchemyAttachmentRepository(session)
            comment_repo = SqlAlchemyCommentRepository(session)

            history_entries = await history_repo.list_for_trip_cursor(
                query.trip_id, dimensao=None, limit=query.limit + 1, after_data_hora=after_data_hora, after_id=None
            )
            occurrences, _ = await occurrence_repo.list_page_for_trip(
                query.trip_id, page=1, limit=query.limit + 1, tipo=None, status=None, gravidade=None
            )
            attachments = await attachment_repo.list_for_entity("VIAGEM", query.trip_id)
            comments = await comment_repo.list_for_entity("VIAGEM", query.trip_id)

        entries: list[TripTimelineEntryDTO] = []
        for entry in history_entries:
            entries.append(
                TripTimelineEntryDTO(
                    occurred_at=entry.data_hora,
                    source=_STATUS_HISTORY_SOURCE[entry.dimensao.value],
                    summary=f"{entry.dimensao.value}: {entry.status}",
                    reference_id=entry.id,
                )
            )
        for occurrence in occurrences:
            if after_data_hora is not None and occurrence.data_hora >= after_data_hora:
                continue
            entries.append(
                TripTimelineEntryDTO(
                    occurred_at=occurrence.data_hora,
                    source="OCORRENCIA",
                    summary=f"Ocorrência registrada: {occurrence.tipo.value}",
                    reference_id=occurrence.id,
                )
            )
        for attachment in attachments:
            if after_data_hora is not None and attachment.criado_em >= after_data_hora:
                continue
            entries.append(
                TripTimelineEntryDTO(
                    occurred_at=attachment.criado_em, source="ANEXO",
                    summary=f"Anexo adicionado: {attachment.tipo_anexo}", reference_id=attachment.id,
                )
            )
        for comment in comments:
            if after_data_hora is not None and comment.criado_em >= after_data_hora:
                continue
            entries.append(
                TripTimelineEntryDTO(
                    occurred_at=comment.criado_em, source="COMENTARIO", summary="Comentário registrado",
                    reference_id=comment.id,
                )
            )

        entries.sort(key=lambda e: e.occurred_at, reverse=True)
        has_more = len(entries) > query.limit
        page = entries[: query.limit]
        next_cursor = _encode_cursor(page[-1].occurred_at) if has_more and page else None

        return ListTripTimelineResult(items=page, next_cursor=next_cursor, has_more=has_more)
