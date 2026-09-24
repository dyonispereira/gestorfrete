from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from modules.freight.application.commands.register_collection import (
    RegisterCollectionCommand,
    RegisterCollectionHandler,
)
from modules.freight.interfaces.schemas.collection_schemas import CollectionResponse, RegisterCollectionRequest
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Collection"])


@router.post("/{trip_id}/coletas", response_model=CollectionResponse, status_code=201)
async def register_collection(
    trip_id: uuid.UUID,
    body: RegisterCollectionRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.pickup.create")),
) -> CollectionResponse:
    handler = RegisterCollectionHandler()
    dto = await handler.handle(
        RegisterCollectionCommand(actor=actor, trip_id=trip_id, conferencia_ok=body.cargo_checked)
    )
    return CollectionResponse.from_dto(dto)
