from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, ValidationError
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.tracking.application.dtos.tracking_event_dto import TrackingEventDTO
from modules.tracking.application.queries.tracking_event_permission_map import EVENT_TYPE_PERMISSION
from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_event_repository import (
    SqlAlchemyTrackingEventRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTrackingEventsQuery(Query):
    actor: AuthenticatedActor
    cursor: str | None = None
    limit: int = 20
    type: str | None = None
    severity: str | None = None
    vehicle_id: uuid.UUID | None = None
    occurred_at_gte: datetime | None = None
    occurred_at_lte: datetime | None = None


@dataclass(frozen=True)
class ListTrackingEventsResult:
    items: list[TrackingEventDTO]
    next_cursor: str | None
    has_more: bool


class ListTrackingEventsHandler(QueryHandler[ListTrackingEventsQuery, ListTrackingEventsResult]):
    """D294 — filtragem por linha: sem `type`, retorna só as categorias cuja permissão o Actor tem
    (nunca `403` genérico); com `type` explícito sem a permissão correspondente, `403`."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._authz = AuthorizationService(session_factory)

    async def handle(self, query: ListTrackingEventsQuery) -> ListTrackingEventsResult:
        after_data_hora, after_id = None, None
        if query.cursor is not None:
            try:
                after_data_hora, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("TRACKING_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        granted_codes = await self._authz.get_permission_codes(query.actor)

        if query.type is not None:
            required = EVENT_TYPE_PERMISSION[TrackingEventType(query.type)]
            if required not in granted_codes:
                raise AuthorizationError(
                    "IDENTITY_PERMISSION_DENIED", f"Ação requer a permissão '{required}'."
                )
            allowed_types = [query.type]
        else:
            allowed_types = [t.value for t, code in EVENT_TYPE_PERMISSION.items() if code in granted_codes]
            if not allowed_types:
                return ListTrackingEventsResult(items=[], next_cursor=None, has_more=False)

        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingEventRepository(session)
            events = await repo.list_page(
                after_data_hora=after_data_hora, after_id=after_id, limit=query.limit + 1, types=allowed_types,
                severity=query.severity, vehicle_id=query.vehicle_id, occurred_at_gte=query.occurred_at_gte,
                occurred_at_lte=query.occurred_at_lte,
            )

        has_more = len(events) > query.limit
        page = events[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].data_hora, id=page[-1].id) if has_more and page else None
        return ListTrackingEventsResult(
            items=[TrackingEventDTO.from_entity(e) for e in page], next_cursor=next_cursor, has_more=has_more
        )
