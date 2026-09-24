from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.commands.create_vehicle_category import (
    CreateVehicleCategoryCommand,
    CreateVehicleCategoryHandler,
)
from modules.fleet.application.commands.update_vehicle_category import (
    UpdateVehicleCategoryCommand,
    UpdateVehicleCategoryHandler,
)
from modules.fleet.application.queries.get_vehicle_category import GetVehicleCategoryHandler, GetVehicleCategoryQuery
from modules.fleet.application.queries.list_vehicle_categories import (
    ListVehicleCategoriesHandler,
    ListVehicleCategoriesQuery,
)
from modules.fleet.domain.value_objects.vehicle_category_status import VehicleCategoryStatus
from modules.fleet.interfaces.schemas.vehicle_category_schemas import (
    CreateVehicleCategoryRequest,
    UpdateVehicleCategoryRequest,
    VehicleCategoryResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/categorias-veiculo", tags=["Vehicle Categories"])


@router.get("")
async def list_vehicle_categories(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_category.view")),
) -> dict[str, Any]:
    handler = ListVehicleCategoriesHandler(get_session_factory())
    result = await handler.handle(
        ListVehicleCategoriesQuery(actor=actor, page=page, limit=limit, status=status, search=search)
    )
    return {
        "data": [VehicleCategoryResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{vehicle_category_id}", response_model=VehicleCategoryResponse)
async def get_vehicle_category(
    vehicle_category_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_category.view")),
) -> VehicleCategoryResponse:
    handler = GetVehicleCategoryHandler(get_session_factory())
    dto = await handler.handle(GetVehicleCategoryQuery(actor=actor, vehicle_category_id=vehicle_category_id))
    return VehicleCategoryResponse.from_dto(dto)


@router.post("", response_model=VehicleCategoryResponse, status_code=201)
async def create_vehicle_category(
    body: CreateVehicleCategoryRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_category.create")),
) -> VehicleCategoryResponse:
    handler = CreateVehicleCategoryHandler()
    dto = await handler.handle(CreateVehicleCategoryCommand(actor=actor, nome=body.nome))
    return VehicleCategoryResponse.from_dto(dto)


@router.patch("/{vehicle_category_id}", response_model=VehicleCategoryResponse)
async def update_vehicle_category(
    vehicle_category_id: uuid.UUID,
    body: UpdateVehicleCategoryRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_category.edit")),
) -> VehicleCategoryResponse:
    handler = UpdateVehicleCategoryHandler()
    dto = await handler.handle(
        UpdateVehicleCategoryCommand(
            actor=actor, vehicle_category_id=vehicle_category_id, nome=body.nome,
            status=VehicleCategoryStatus(body.status) if body.status else None,
        )
    )
    return VehicleCategoryResponse.from_dto(dto)


# Sem DELETE — RBAC_MATRIX.md não tem fleet.vehicle_category.delete (mesmo padrão de CostCenter)
