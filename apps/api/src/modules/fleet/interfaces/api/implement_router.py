from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.commands.create_implement import CreateImplementCommand, CreateImplementHandler
from modules.fleet.application.commands.deactivate_implement import (
    DeactivateImplementCommand,
    DeactivateImplementHandler,
)
from modules.fleet.application.commands.update_implement import UpdateImplementCommand, UpdateImplementHandler
from modules.fleet.application.queries.get_implement import GetImplementHandler, GetImplementQuery
from modules.fleet.application.queries.list_implements import ListImplementsHandler, ListImplementsQuery
from modules.fleet.domain.value_objects.body_type import BodyType
from modules.fleet.domain.value_objects.implement_availability import ImplementAvailability
from modules.fleet.interfaces.schemas.implement_schemas import (
    CreateImplementRequest,
    ImplementResponse,
    UpdateImplementRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/implementos", tags=["Implements"])


@router.get("")
async def list_implements(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    tipo_carroceria: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.implement.view")),
) -> dict[str, Any]:
    handler = ListImplementsHandler(get_session_factory())
    result = await handler.handle(
        ListImplementsQuery(actor=actor, page=page, limit=limit, search=search, tipo_carroceria=tipo_carroceria, status=status)
    )
    return {
        "data": [ImplementResponse.from_dto(i) for i in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{implement_id}", response_model=ImplementResponse)
async def get_implement(
    implement_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.implement.view")),
) -> ImplementResponse:
    handler = GetImplementHandler(get_session_factory())
    dto = await handler.handle(GetImplementQuery(actor=actor, implement_id=implement_id))
    return ImplementResponse.from_dto(dto)


@router.post("", response_model=ImplementResponse, status_code=201)
async def create_implement(
    body: CreateImplementRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.implement.create")),
) -> ImplementResponse:
    handler = CreateImplementHandler()
    dto = await handler.handle(
        CreateImplementCommand(
            actor=actor, placa=body.plate, renavam=body.renavam, body_type=BodyType(body.body_type),
            category_id=body.category_id, load_capacity=body.load_capacity,
        )
    )
    return ImplementResponse.from_dto(dto)


@router.patch("/{implement_id}", response_model=ImplementResponse)
async def update_implement(
    implement_id: uuid.UUID,
    body: UpdateImplementRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.implement.edit")),
) -> ImplementResponse:
    handler = UpdateImplementHandler()
    dto = await handler.handle(
        UpdateImplementCommand(
            actor=actor,
            implement_id=implement_id,
            body_type=BodyType(body.body_type) if body.body_type else None,
            load_capacity=body.load_capacity,
            availability_status=ImplementAvailability(body.availability_status) if body.availability_status else None,
        )
    )
    return ImplementResponse.from_dto(dto)


@router.delete("/{implement_id}", status_code=204, response_model=None)
async def deactivate_implement(
    implement_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.implement.delete")),
) -> None:
    handler = DeactivateImplementHandler()
    await handler.handle(DeactivateImplementCommand(actor=actor, implement_id=implement_id))
