from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.commands.create_vehicle_composition import (
    CreateVehicleCompositionCommand,
    CreateVehicleCompositionHandler,
)
from modules.fleet.application.commands.validate_vehicle_composition import (
    ValidateVehicleCompositionCommand,
    ValidateVehicleCompositionHandler,
)
from modules.fleet.application.queries.get_vehicle_composition import (
    GetVehicleCompositionHandler,
    GetVehicleCompositionQuery,
)
from modules.fleet.application.queries.list_vehicle_compositions import (
    ListVehicleCompositionsHandler,
    ListVehicleCompositionsQuery,
)
from modules.fleet.domain.value_objects.combination_type import CombinationType
from modules.fleet.interfaces.schemas.vehicle_composition_schemas import (
    CreateVehicleCompositionRequest,
    VehicleCompositionResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/vehicle-compositions", tags=["Vehicle Compositions"])


@router.get("")
async def list_vehicle_compositions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    veiculo_tracionador_id: uuid.UUID | None = None,
    tipo_combinacao: str | None = None,
    vigente: bool = True,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_composition.view")),
) -> dict[str, Any]:
    handler = ListVehicleCompositionsHandler(get_session_factory())
    result = await handler.handle(
        ListVehicleCompositionsQuery(
            actor=actor, page=page, limit=limit, veiculo_tracionador_id=veiculo_tracionador_id,
            tipo_combinacao=tipo_combinacao, vigente=vigente,
        )
    )
    return {
        "data": [VehicleCompositionResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{composition_id}", response_model=VehicleCompositionResponse)
async def get_vehicle_composition(
    composition_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_composition.view")),
) -> VehicleCompositionResponse:
    handler = GetVehicleCompositionHandler(get_session_factory())
    dto = await handler.handle(GetVehicleCompositionQuery(actor=actor, composition_id=composition_id))
    return VehicleCompositionResponse.from_dto(dto)


@router.post("", response_model=VehicleCompositionResponse, status_code=201)
async def create_vehicle_composition(
    body: CreateVehicleCompositionRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_composition.create")),
) -> VehicleCompositionResponse:
    handler = CreateVehicleCompositionHandler()
    dto = await handler.handle(
        CreateVehicleCompositionCommand(
            actor=actor,
            tractor_unit_id=body.tractor_unit_id,
            combination_type=CombinationType(body.combination_type),
            total_axles=body.total_axles,
            implements=[(item.implement_id, item.order) for item in body.implements],
        )
    )
    return VehicleCompositionResponse.from_dto(dto)


@router.post("/{composition_id}/commands/validate", response_model=VehicleCompositionResponse)
async def validate_vehicle_composition(
    composition_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_composition.validate")),
) -> VehicleCompositionResponse:
    handler = ValidateVehicleCompositionHandler()
    dto = await handler.handle(ValidateVehicleCompositionCommand(actor=actor, composition_id=composition_id))
    return VehicleCompositionResponse.from_dto(dto)


# Sem PATCH/DELETE — D248 (nunca edita in-place, sem fleet.vehicle_composition.edit/.delete em RBAC)
