from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.queries.list_tracking_history import (
    ListTrackingHistoryHandler,
    ListTrackingHistoryQuery,
)
from modules.tracking.interfaces.schemas.tracking_history_schemas import TrackingHistoryEntryResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/vehicles/{vehicle_id}/tracking", tags=["Tracking History"])


@router.get("/history")
async def list_history(
    vehicle_id: uuid.UUID,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.position.view")),
) -> dict[str, Any]:
    handler = ListTrackingHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListTrackingHistoryQuery(
            actor=actor, vehicle_id=vehicle_id, period_start=period_start, period_end=period_end,
            cursor=cursor, limit=limit, source=source,
        )
    )
    return {
        "data": [TrackingHistoryEntryResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
