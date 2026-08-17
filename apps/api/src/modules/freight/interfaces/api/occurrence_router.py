from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.commands.create_occurrence import CreateOccurrenceCommand, CreateOccurrenceHandler
from modules.freight.application.commands.update_occurrence import UpdateOccurrenceCommand, UpdateOccurrenceHandler
from modules.freight.application.queries.get_occurrence import GetOccurrenceHandler, GetOccurrenceQuery
from modules.freight.application.queries.list_occurrences import ListOccurrencesHandler, ListOccurrencesQuery
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_status import OccurrenceStatus
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from modules.freight.interfaces.schemas.occurrence_schemas import (
    CreateOccurrenceRequest,
    OccurrenceResponse,
    UpdateOccurrenceRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Occurrences"])


@router.get("/{trip_id}/occurrences")
async def list_occurrences(
    trip_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.view")),
) -> dict[str, Any]:
    handler = ListOccurrencesHandler(get_session_factory())
    result = await handler.handle(
        ListOccurrencesQuery(actor=actor, trip_id=trip_id, page=page, limit=limit, tipo=type, status=status, gravidade=severity)
    )
    return {
        "data": [OccurrenceResponse.from_dto(o) for o in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{trip_id}/occurrences/{occurrence_id}", response_model=OccurrenceResponse)
async def get_occurrence(
    trip_id: uuid.UUID,
    occurrence_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.view")),
) -> OccurrenceResponse:
    handler = GetOccurrenceHandler(get_session_factory())
    dto = await handler.handle(GetOccurrenceQuery(actor=actor, trip_id=trip_id, occurrence_id=occurrence_id))
    return OccurrenceResponse.from_dto(dto)


@router.post("/{trip_id}/occurrences", response_model=OccurrenceResponse, status_code=201)
async def create_occurrence(
    trip_id: uuid.UUID,
    body: CreateOccurrenceRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.create")),
) -> OccurrenceResponse:
    handler = CreateOccurrenceHandler()
    dto = await handler.handle(
        CreateOccurrenceCommand(
            actor=actor, trip_id=trip_id, tipo=OccurrenceType(body.type), descricao=body.description,
            gravidade=OccurrenceSeverity(body.severity) if body.severity else None, occurred_at=body.occurred_at,
        )
    )
    return OccurrenceResponse.from_dto(dto)


@router.patch("/{trip_id}/occurrences/{occurrence_id}", response_model=OccurrenceResponse)
async def update_occurrence(
    trip_id: uuid.UUID,
    occurrence_id: uuid.UUID,
    body: UpdateOccurrenceRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.edit")),
) -> OccurrenceResponse:
    handler = UpdateOccurrenceHandler()
    dto = await handler.handle(
        UpdateOccurrenceCommand(
            actor=actor, trip_id=trip_id, occurrence_id=occurrence_id, descricao=body.description,
            gravidade=OccurrenceSeverity(body.severity) if body.severity else None,
            status=OccurrenceStatus(body.status) if body.status else None,
        )
    )
    return OccurrenceResponse.from_dto(dto)
