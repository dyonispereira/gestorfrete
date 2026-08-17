from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.commands.register_odometer_reading import (
    RegisterOdometerReadingCommand,
    RegisterOdometerReadingHandler,
)
from modules.fleet.application.queries.list_odometer_readings import (
    ListOdometerReadingsHandler,
    ListOdometerReadingsQuery,
)
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.fleet.interfaces.schemas.odometer_reading_schemas import (
    CreateOdometerReadingRequest,
    OdometerReadingResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/veiculos", tags=["Odometer Readings"])


@router.get("/{vehicle_id}/odometro/leituras")
async def list_odometer_readings(
    vehicle_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    origem: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.odometer_reading.view")),
) -> dict[str, Any]:
    handler = ListOdometerReadingsHandler(get_session_factory())
    result = await handler.handle(
        ListOdometerReadingsQuery(actor=actor, vehicle_id=vehicle_id, cursor=cursor, limit=limit, origem=origem)
    )
    return {
        "data": [OdometerReadingResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.post("/{vehicle_id}/odometro/leituras", response_model=OdometerReadingResponse, status_code=201)
async def create_odometer_reading(
    vehicle_id: uuid.UUID,
    body: CreateOdometerReadingRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.odometer_reading.create")),
) -> OdometerReadingResponse:
    handler = RegisterOdometerReadingHandler()
    dto = await handler.handle(
        RegisterOdometerReadingCommand(
            actor=actor, vehicle_id=vehicle_id, value_km=body.value_km, origin=OdometerOrigin(body.origin),
            trip_id=body.trip_id,
        )
    )
    return OdometerReadingResponse.from_dto(dto)
