from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.commands.create_occurrence import CreateOccurrenceCommand, CreateOccurrenceHandler
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from modules.freight.interfaces.schemas.occurrence_schemas import CreateOccurrenceRequest, OccurrenceResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.queries.list_own_occurrences import (
    ListOwnOccurrencesHandler,
    ListOwnOccurrencesQuery,
)
from modules.mobile.application.queries.ownership import assert_owns_trip
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.interfaces.dependencies import get_current_mobile_session
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/trips", tags=["Mobile Occurrences"])


@router.get("/{trip_id}/occurrences")
async def list_own_occurrences(
    trip_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.view")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> dict[str, Any]:
    handler = ListOwnOccurrencesHandler(get_session_factory())
    result = await handler.handle(
        ListOwnOccurrencesQuery(
            actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id, page=page, limit=limit
        )
    )
    return {
        "data": [OccurrenceResponse.from_dto(o) for o in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.post("/{trip_id}/occurrences", response_model=OccurrenceResponse, status_code=201)
async def create_own_occurrence(
    trip_id: uuid.UUID, body: CreateOccurrenceRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.occurrence.create")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> OccurrenceResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await CreateOccurrenceHandler().handle(
        CreateOccurrenceCommand(
            actor=actor, trip_id=trip_id, tipo=OccurrenceType(body.type), descricao=body.description,
            gravidade=OccurrenceSeverity(body.severity) if body.severity else None, occurred_at=body.occurred_at,
        )
    )
    return OccurrenceResponse.from_dto(dto)
