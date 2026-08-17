from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import ValidationError
from modules.ai.application.dtos.ai_inference_dto import AIInferenceDTO
from modules.ai.application.queries.get_inference import VIEW_COST_PERMISSION
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_inference_repository import (
    SqlAlchemyAIInferenceRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListInferencesQuery(Query):
    actor: AuthenticatedActor
    held_permissions: frozenset[str]
    cursor: str | None = None
    limit: int = 20
    model_id: uuid.UUID | None = None
    status: str | None = None
    origin: str | None = None
    started_at_from: datetime | None = None
    started_at_to: datetime | None = None


@dataclass(frozen=True)
class ListInferencesResult:
    items: list[AIInferenceDTO]
    next_cursor: str | None
    has_more: bool


class ListInferencesHandler(QueryHandler[ListInferencesQuery, ListInferencesResult]):
    """`072` — cursor pagination (`inferencias_ia` é Time Series/Alto volume, mesmo critério de
    `eventos_fiscais`)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListInferencesQuery) -> ListInferencesResult:
        cursor_data_hora = None
        cursor_id = None
        if query.cursor is not None:
            try:
                cursor_data_hora, cursor_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("AI_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            repo = SqlAlchemyAIInferenceRepository(session)
            inferences = await repo.list_page(
                cursor_data_hora=cursor_data_hora, cursor_id=cursor_id, limit=query.limit + 1,
                modelo_ia_id=query.model_id, status=query.status, origem=query.origin,
                started_at_from=query.started_at_from, started_at_to=query.started_at_to,
            )

        has_more = len(inferences) > query.limit
        page = inferences[: query.limit]
        next_cursor = (
            encode_cursor(data_hora=page[-1].data_hora_inicio, id=page[-1].id) if has_more and page else None
        )
        has_cost = VIEW_COST_PERMISSION in query.held_permissions
        return ListInferencesResult(
            items=[AIInferenceDTO.from_entity(i, has_cost_permission=has_cost) for i in page],
            next_cursor=next_cursor, has_more=has_more,
        )
