from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.queries.get_vehicle_availability import (
    GetVehicleAvailabilityHandler,
    GetVehicleAvailabilityQuery,
)
from modules.fleet.application.queries.list_vehicle_availability import (
    ListVehicleAvailabilityHandler,
    ListVehicleAvailabilityQuery,
)
from modules.fleet.interfaces.schemas.vehicle_availability_schemas import VehicleAvailabilityResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/veiculos", tags=["Vehicle Availability"])

# D247 — nenhum comando de escrita. Só os dois GETs abaixo existem neste arquivo, em todo o
# projeto — confirmar isso é uma das duas auditorias explicitamente pedidas pelo usuário para
# fechar o Lote 4 (`AVAILABILITY_IMPLEMENTATION.md`).
#
# Registrado em `interfaces/api/v1/router.py` **antes** de `vehicle_router` (mesmo motivo de
# `/drivers/me` vs `/drivers/{id}`, Lote 3): sem isso, `GET /veiculos/disponibilidade` seria
# capturado por `GET /veiculos/{vehicle_id}` e falharia a validação de UUID.


@router.get("/disponibilidade")
async def list_vehicle_availability(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.view_availability")),
) -> dict[str, Any]:
    handler = ListVehicleAvailabilityHandler(get_session_factory())
    result = await handler.handle(ListVehicleAvailabilityQuery(actor=actor, page=page, limit=limit, status=status))
    return {
        "data": [VehicleAvailabilityResponse.from_dto(a) for a in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{vehicle_id}/disponibilidade", response_model=VehicleAvailabilityResponse)
async def get_vehicle_availability(
    vehicle_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.view_availability")),
) -> VehicleAvailabilityResponse:
    handler = GetVehicleAvailabilityHandler(get_session_factory())
    dto = await handler.handle(GetVehicleAvailabilityQuery(actor=actor, vehicle_id=vehicle_id))
    return VehicleAvailabilityResponse.from_dto(dto)
