from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.queries.list_vehicle_positions import (
    ListVehiclePositionsHandler,
    ListVehiclePositionsQuery,
)
from modules.tracking.interfaces.schemas.vehicle_position_schemas import VehiclePositionResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/vehicles/{vehicle_id}/tracking", tags=["Vehicle Positions"])


@router.get("/positions")
async def list_positions(
    vehicle_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    captured_at__gte: datetime | None = None,
    captured_at__lte: datetime | None = None,
    origin: uuid.UUID | None = None,
    equipment_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.position.view")),
) -> dict[str, Any]:
    handler = ListVehiclePositionsHandler(get_session_factory())
    result = await handler.handle(
        ListVehiclePositionsQuery(
            actor=actor, vehicle_id=vehicle_id, cursor=cursor, limit=limit, captured_at_gte=captured_at__gte,
            captured_at_lte=captured_at__lte, origin_id=origin, equipment_id=equipment_id,
        )
    )
    return {
        "data": [VehiclePositionResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
