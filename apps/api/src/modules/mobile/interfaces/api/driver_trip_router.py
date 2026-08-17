from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.commands.accept_trip import AcceptTripCommand, AcceptTripHandler
from modules.freight.application.commands.dispatch_trip import DispatchTripCommand, DispatchTripHandler
from modules.freight.application.commands.finish_trip import FinishTripCommand, FinishTripHandler
from modules.freight.application.commands.interromper_trip import InterromperTripCommand, InterromperTripHandler
from modules.freight.application.commands.retomar_trip import RetomarTripCommand, RetomarTripHandler
from modules.freight.interfaces.schemas.trip_schemas import InterromperTripRequest, TripResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.queries.get_own_trip import GetOwnTripHandler, GetOwnTripQuery
from modules.mobile.application.queries.list_own_trips import ListOwnTripsHandler, ListOwnTripsQuery
from modules.mobile.application.queries.ownership import assert_owns_trip
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.interfaces.dependencies import get_current_mobile_session
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/trips", tags=["Mobile Trips"])


@router.get("")
async def list_own_trips(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view_own")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> dict[str, Any]:
    handler = ListOwnTripsHandler(get_session_factory())
    result = await handler.handle(
        ListOwnTripsQuery(
            actor=actor, driver_id=mobile_session.motorista_id, page=page, limit=limit, status_operacional=status
        )
    )
    return {
        "data": [TripResponse.from_dto(t) for t in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{trip_id}", response_model=TripResponse)
async def get_own_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.view_own")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    handler = GetOwnTripHandler(get_session_factory())
    dto = await handler.handle(GetOwnTripQuery(actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/accept", response_model=TripResponse)
async def accept_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await AcceptTripHandler().handle(AcceptTripCommand(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/start", response_model=TripResponse)
async def start_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.start")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await DispatchTripHandler().handle(
        DispatchTripCommand(actor=actor, trip_id=trip_id, origin="app_motorista")
    )
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/interromper", response_model=TripResponse)
async def interromper_trip(
    trip_id: uuid.UUID, body: InterromperTripRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await InterromperTripHandler().handle(
        InterromperTripCommand(actor=actor, trip_id=trip_id, notes=body.notes)
    )
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/retomar", response_model=TripResponse)
async def retomar_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await RetomarTripHandler().handle(RetomarTripCommand(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/finish", response_model=TripResponse)
async def finish_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.finish")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> TripResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await FinishTripHandler().handle(FinishTripCommand(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)
