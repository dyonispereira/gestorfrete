from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.queries.list_trip_timeline import ListTripTimelineHandler, ListTripTimelineQuery
from modules.freight.interfaces.schemas.timeline_schemas import TripTimelineEntryResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Timeline"])

# D187/D236 — só este GET existe neste arquivo, em todo o projeto: a Timeline nunca tem caminho de
# escrita (`TIMELINE_IMPLEMENTATION.md`).


@router.get("/{trip_id}/timeline")
async def list_trip_timeline(
    trip_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view")),
) -> dict[str, Any]:
    handler = ListTripTimelineHandler(get_session_factory())
    result = await handler.handle(ListTripTimelineQuery(actor=actor, trip_id=trip_id, cursor=cursor, limit=limit))
    return {
        "data": [TripTimelineEntryResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
