from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.queries.list_heartbeats import ListHeartbeatsHandler, ListHeartbeatsQuery
from modules.tracking.interfaces.schemas.heartbeat_schemas import HeartbeatResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tracking/equipment", tags=["Heartbeats"])


@router.get("/{equipment_id}/heartbeats")
async def list_heartbeats(
    equipment_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    received_at__gte: datetime | None = None,
    received_at__lte: datetime | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.heartbeat.view")),
) -> dict[str, Any]:
    handler = ListHeartbeatsHandler(get_session_factory())
    result = await handler.handle(
        ListHeartbeatsQuery(
            actor=actor, equipment_id=equipment_id, cursor=cursor, limit=limit,
            received_at_gte=received_at__gte, received_at_lte=received_at__lte,
        )
    )
    return {
        "data": [HeartbeatResponse.from_dto(h) for h in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
