from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.commands.accept_trip import AcceptTripCommand, AcceptTripHandler
from modules.freight.application.commands.cancelar_trip import CancelarTripCommand, CancelarTripHandler
from modules.freight.application.commands.close_administrative_trip import (
    CloseAdministrativeTripCommand,
    CloseAdministrativeTripHandler,
)
from modules.freight.application.commands.create_trip import CreateTripCommand, CreateTripHandler
from modules.freight.application.commands.create_trip_allocation import (
    CreateTripAllocationCommand,
    CreateTripAllocationHandler,
)
from modules.freight.application.commands.delete_trip import DeleteTripCommand, DeleteTripHandler
from modules.freight.application.commands.dispatch_trip import DispatchTripCommand, DispatchTripHandler
from modules.freight.application.commands.finish_trip import FinishTripCommand, FinishTripHandler
from modules.freight.application.commands.interromper_trip import InterromperTripCommand, InterromperTripHandler
from modules.freight.application.commands.reallocate_trip_resources import (
    ReallocateTripResourcesCommand,
    ReallocateTripResourcesHandler,
)
from modules.freight.application.commands.retomar_trip import RetomarTripCommand, RetomarTripHandler
from modules.freight.application.commands.update_trip import UpdateTripCommand, UpdateTripHandler
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from modules.freight.application.queries.get_trip_allocations import (
    GetTripAllocationsHandler,
    GetTripAllocationsQuery,
)
from modules.freight.application.queries.list_trips import ListTripsHandler, ListTripsQuery
from modules.freight.interfaces.schemas.trip_allocation_schemas import (
    CreateTripAllocationRequest,
    ReallocateTripResourcesRequest,
    TripAllocationResponse,
)
from modules.freight.interfaces.schemas.trip_schemas import (
    CancelarTripRequest,
    CloseAdministrativeTripRequest,
    CreateTripRequest,
    DispatchTripRequest,
    FinishTripRequest,
    InterromperTripRequest,
    TripResponse,
    UpdateTripRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trips"])


@router.get("")
async def list_trips(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_operacional: str | None = None,
    status_fiscal: str | None = None,
    status_financeiro: str | None = None,
    motorista_id: uuid.UUID | None = None,
    veiculo_id: uuid.UUID | None = None,
    cliente_id: uuid.UUID | None = None,
    data_programada: date | None = None,
    codigo: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view")),
) -> dict[str, Any]:
    handler = ListTripsHandler(get_session_factory())
    result = await handler.handle(
        ListTripsQuery(
            actor=actor, page=page, limit=limit, status_operacional=status_operacional, status_fiscal=status_fiscal,
            status_financeiro=status_financeiro, motorista_id=motorista_id, veiculo_id=veiculo_id,
            cliente_id=cliente_id, data_programada=data_programada, codigo=codigo,
        )
    )
    return {
        "data": [TripResponse.from_dto(t) for t in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.view"))
) -> TripResponse:
    handler = GetTripHandler(get_session_factory())
    dto = await handler.handle(GetTripQuery(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("", response_model=TripResponse, status_code=201)
async def create_trip(
    body: CreateTripRequest, actor: AuthenticatedActor = Depends(require_permission("freight.trip.create"))
) -> TripResponse:
    handler = CreateTripHandler()
    dto = await handler.handle(
        CreateTripCommand(
            actor=actor, cliente_id=body.cliente_id, data_programada=body.data_programada,
            janela_programada=body.janela_programada,
        )
    )
    return TripResponse.from_dto(dto)


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: uuid.UUID, body: UpdateTripRequest, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit"))
) -> TripResponse:
    handler = UpdateTripHandler()
    dto = await handler.handle(
        UpdateTripCommand(
            actor=actor, trip_id=trip_id, data_programada=body.data_programada, janela_programada=body.janela_programada
        )
    )
    return TripResponse.from_dto(dto)


@router.delete("/{trip_id}", status_code=204, response_model=None)
async def delete_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit"))
) -> None:
    handler = DeleteTripHandler()
    await handler.handle(DeleteTripCommand(actor=actor, trip_id=trip_id))


# --- Alocação de Recursos (D188) ---


@router.get("/{trip_id}/resources")
async def get_trip_resources(
    trip_id: uuid.UUID,
    history: bool = False,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view")),
) -> dict[str, Any]:
    handler = GetTripAllocationsHandler(get_session_factory())
    result = await handler.handle(GetTripAllocationsQuery(actor=actor, trip_id=trip_id, history=history))
    if not history:
        assert result.current is not None
        return TripAllocationResponse.from_dto(result.current).model_dump(mode="json")
    return {
        "data": [TripAllocationResponse.from_dto(a) for a in result.items],
        "meta": {"pagination": {"page": 1, "limit": len(result.items), "total": len(result.items)}},
    }


@router.post("/{trip_id}/resources", response_model=TripAllocationResponse, status_code=201)
async def create_trip_resources(
    trip_id: uuid.UUID,
    body: CreateTripAllocationRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
) -> TripAllocationResponse:
    handler = CreateTripAllocationHandler()
    dto = await handler.handle(
        CreateTripAllocationCommand(
            actor=actor, trip_id=trip_id, driver_id=body.driver_id, tractor_unit_id=body.tractor_unit_id,
            implement_id=body.implement_id,
        )
    )
    return TripAllocationResponse.from_dto(dto)


@router.post("/{trip_id}/commands/reallocate-resources", response_model=TripAllocationResponse)
async def reallocate_trip_resources(
    trip_id: uuid.UUID,
    body: ReallocateTripResourcesRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.reassign")),
) -> TripAllocationResponse:
    handler = ReallocateTripResourcesHandler()
    dto = await handler.handle(
        ReallocateTripResourcesCommand(
            actor=actor, trip_id=trip_id, driver_id=body.driver_id, tractor_unit_id=body.tractor_unit_id,
            implement_id=body.implement_id, reason=body.reason,
        )
    )
    return TripAllocationResponse.from_dto(dto)


# --- Comandos de Status Operacional (018-trip-status.md) ---


@router.post("/{trip_id}/commands/accept", response_model=TripResponse)
async def accept_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit"))
) -> TripResponse:
    handler = AcceptTripHandler()
    dto = await handler.handle(AcceptTripCommand(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/dispatch", response_model=TripResponse)
async def dispatch_trip(
    trip_id: uuid.UUID, body: DispatchTripRequest | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.dispatch")),
) -> TripResponse:
    handler = DispatchTripHandler()
    dto = await handler.handle(
        DispatchTripCommand(
            actor=actor, trip_id=trip_id, origin="portal_gestor",
            hodometro_saida_km=body.departure_odometer_km if body is not None else None,
        )
    )
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/start", response_model=TripResponse)
async def start_trip(
    trip_id: uuid.UUID, body: DispatchTripRequest | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.start")),
) -> TripResponse:
    handler = DispatchTripHandler()
    dto = await handler.handle(
        DispatchTripCommand(
            actor=actor, trip_id=trip_id, origin="app_motorista",
            hodometro_saida_km=body.departure_odometer_km if body is not None else None,
        )
    )
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/finish", response_model=TripResponse)
async def finish_trip(
    trip_id: uuid.UUID, body: FinishTripRequest | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.finish")),
) -> TripResponse:
    handler = FinishTripHandler()
    dto = await handler.handle(
        FinishTripCommand(
            actor=actor, trip_id=trip_id,
            hodometro_chegada_km=body.arrival_odometer_km if body is not None else None,
        )
    )
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/interromper", response_model=TripResponse)
async def interromper_trip(
    trip_id: uuid.UUID,
    body: InterromperTripRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
) -> TripResponse:
    handler = InterromperTripHandler()
    dto = await handler.handle(InterromperTripCommand(actor=actor, trip_id=trip_id, notes=body.notes))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/retomar", response_model=TripResponse)
async def retomar_trip(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit"))
) -> TripResponse:
    handler = RetomarTripHandler()
    dto = await handler.handle(RetomarTripCommand(actor=actor, trip_id=trip_id))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/cancelar", response_model=TripResponse)
async def cancelar_trip(
    trip_id: uuid.UUID,
    body: CancelarTripRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.cancel")),
) -> TripResponse:
    handler = CancelarTripHandler()
    dto = await handler.handle(CancelarTripCommand(actor=actor, trip_id=trip_id, notes=body.notes))
    return TripResponse.from_dto(dto)


@router.post("/{trip_id}/commands/close-administrative", response_model=TripResponse)
async def close_administrative_trip(
    trip_id: uuid.UUID,
    body: CloseAdministrativeTripRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.close")),
) -> TripResponse:
    handler = CloseAdministrativeTripHandler()
    dto = await handler.handle(
        CloseAdministrativeTripCommand(actor=actor, trip_id=trip_id, justification=body.justification)
    )
    return TripResponse.from_dto(dto)
