from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.commands.create_tracking_equipment import (
    CreateTrackingEquipmentCommand,
    CreateTrackingEquipmentHandler,
)
from modules.tracking.application.commands.update_tracking_equipment import (
    UpdateTrackingEquipmentCommand,
    UpdateTrackingEquipmentHandler,
)
from modules.tracking.application.queries.get_tracking_equipment import (
    GetTrackingEquipmentHandler,
    GetTrackingEquipmentQuery,
)
from modules.tracking.application.queries.list_tracking_equipment import (
    ListTrackingEquipmentHandler,
    ListTrackingEquipmentQuery,
)
from modules.tracking.domain.value_objects.equipment_status import EquipmentStatus
from modules.tracking.domain.value_objects.equipment_type import EquipmentType
from modules.tracking.interfaces.schemas.tracking_equipment_schemas import (
    CreateTrackingEquipmentRequest,
    TrackingEquipmentResponse,
    UpdateTrackingEquipmentRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tracking/equipment", tags=["Tracking Equipment"])


@router.get("")
async def list_equipment(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    vehicle_id: uuid.UUID | None = None,
    provider_id: uuid.UUID | None = None,
    equipment_type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.equipment.view")),
) -> dict[str, Any]:
    handler = ListTrackingEquipmentHandler(get_session_factory())
    result = await handler.handle(
        ListTrackingEquipmentQuery(
            actor=actor, page=page, limit=limit, vehicle_id=vehicle_id, provider_id=provider_id,
            equipment_type=equipment_type, status=status,
        )
    )
    return {
        "data": [TrackingEquipmentResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{equipment_id}", response_model=TrackingEquipmentResponse)
async def get_equipment(
    equipment_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("tracking.equipment.view"))
) -> TrackingEquipmentResponse:
    handler = GetTrackingEquipmentHandler(get_session_factory())
    dto = await handler.handle(GetTrackingEquipmentQuery(actor=actor, equipment_id=equipment_id))
    return TrackingEquipmentResponse.from_dto(dto)


@router.post("", response_model=TrackingEquipmentResponse, status_code=201)
async def create_equipment(
    body: CreateTrackingEquipmentRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.equipment.create")),
) -> TrackingEquipmentResponse:
    handler = CreateTrackingEquipmentHandler()
    dto = await handler.handle(
        CreateTrackingEquipmentCommand(
            actor=actor, provider_id=body.provider_id, serial_identifier=body.serial_identifier,
            equipment_type=EquipmentType(body.equipment_type), vehicle_id=body.vehicle_id,
        )
    )
    return TrackingEquipmentResponse.from_dto(dto)


@router.patch("/{equipment_id}", response_model=TrackingEquipmentResponse)
async def update_equipment(
    equipment_id: uuid.UUID, body: UpdateTrackingEquipmentRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.equipment.edit")),
) -> TrackingEquipmentResponse:
    handler = UpdateTrackingEquipmentHandler()
    status = EquipmentStatus(body.status) if body.status is not None else None
    dto = await handler.handle(
        UpdateTrackingEquipmentCommand(
            actor=actor, equipment_id=equipment_id, vehicle_id=body.vehicle_id, ends_at=body.ends_at, status=status
        )
    )
    return TrackingEquipmentResponse.from_dto(dto)
