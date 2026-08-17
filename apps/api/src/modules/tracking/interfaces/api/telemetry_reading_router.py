from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.queries.list_telemetry_readings import (
    ListTelemetryReadingsHandler,
    ListTelemetryReadingsQuery,
)
from modules.tracking.interfaces.schemas.telemetry_reading_schemas import TelemetryReadingResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/vehicles/{vehicle_id}/tracking", tags=["Telemetry Readings"])


@router.get("/telemetry")
async def list_telemetry(
    vehicle_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    sensor_type: str | None = None,
    captured_at__gte: datetime | None = None,
    captured_at__lte: datetime | None = None,
    equipment_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.telemetry.view")),
) -> dict[str, Any]:
    handler = ListTelemetryReadingsHandler(get_session_factory())
    result = await handler.handle(
        ListTelemetryReadingsQuery(
            actor=actor, vehicle_id=vehicle_id, cursor=cursor, limit=limit, sensor_type=sensor_type,
            captured_at_gte=captured_at__gte, captured_at_lte=captured_at__lte, equipment_id=equipment_id,
        )
    )
    return {
        "data": [TelemetryReadingResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
