from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.tracking.application.queries.get_tracking_event import GetTrackingEventHandler, GetTrackingEventQuery
from modules.tracking.application.queries.list_tracking_events import (
    ListTrackingEventsHandler,
    ListTrackingEventsQuery,
)
from modules.tracking.interfaces.schemas.tracking_event_schemas import TrackingEventResponse
from shared_kernel.domain.actor import AuthenticatedActor

# D294 — sem permissão única para a coleção: a filtragem por linha acontece no Query Handler
# (`ListTrackingEventsHandler`), não num `require_permission(...)` fixo neste router — só exige
# autenticação (`get_current_actor`), mesmo padrão de `019-trip-timeline.md`.
from interfaces.dependencies.auth import get_current_actor

router = APIRouter(prefix="/tracking/events", tags=["Tracking Events"])


@router.get("")
async def list_events(
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    severity: str | None = None,
    vehicle_id: uuid.UUID | None = None,
    occurred_at__gte: datetime | None = None,
    occurred_at__lte: datetime | None = None,
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> dict[str, Any]:
    handler = ListTrackingEventsHandler(get_session_factory())
    result = await handler.handle(
        ListTrackingEventsQuery(
            actor=actor, cursor=cursor, limit=limit, type=type, severity=severity, vehicle_id=vehicle_id,
            occurred_at_gte=occurred_at__gte, occurred_at_lte=occurred_at__lte,
        )
    )
    return {
        "data": [TrackingEventResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.get("/{event_id}", response_model=TrackingEventResponse)
async def get_event(
    event_id: uuid.UUID, actor: AuthenticatedActor = Depends(get_current_actor)
) -> TrackingEventResponse:
    handler = GetTrackingEventHandler(get_session_factory())
    dto = await handler.handle(GetTrackingEventQuery(actor=actor, event_id=event_id))
    return TrackingEventResponse.from_dto(dto)
