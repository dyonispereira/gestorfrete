from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from modules.freight.application.commands.create_delivery import CreateDeliveryCommand, CreateDeliveryHandler
from modules.freight.application.commands.register_proof_of_delivery import (
    RegisterProofOfDeliveryCommand,
    RegisterProofOfDeliveryHandler,
)
from modules.freight.application.commands.update_delivery import UpdateDeliveryCommand, UpdateDeliveryHandler
from modules.freight.application.queries.get_delivery import GetDeliveryHandler, GetDeliveryQuery
from modules.freight.application.queries.list_deliveries import ListDeliveriesHandler, ListDeliveriesQuery
from modules.freight.domain.value_objects.delivery_status import DeliveryStatus
from modules.freight.interfaces.schemas.delivery_schemas import (
    CreateDeliveryRequest,
    DeliveryResponse,
    ProofOfDeliveryResponse,
    RegisterProofOfDeliveryRequest,
    UpdateDeliveryRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Deliveries"])


@router.get("/{trip_id}/entregas")
async def list_deliveries(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view"))
) -> dict[str, Any]:
    handler = ListDeliveriesHandler(get_session_factory())
    items = await handler.handle(ListDeliveriesQuery(actor=actor, trip_id=trip_id))
    return {
        "data": [DeliveryResponse.from_dto(d) for d in items],
        "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}},
    }


@router.get("/{trip_id}/entregas/{entrega_id}", response_model=DeliveryResponse)
async def get_delivery(
    trip_id: uuid.UUID,
    entrega_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view")),
) -> DeliveryResponse:
    handler = GetDeliveryHandler(get_session_factory())
    dto = await handler.handle(GetDeliveryQuery(actor=actor, trip_id=trip_id, delivery_id=entrega_id))
    return DeliveryResponse.from_dto(dto)


@router.post("/{trip_id}/entregas", response_model=DeliveryResponse, status_code=201)
async def create_delivery(
    trip_id: uuid.UUID,
    body: CreateDeliveryRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.delivery.create")),
) -> DeliveryResponse:
    handler = CreateDeliveryHandler()
    dto = await handler.handle(
        CreateDeliveryCommand(
            actor=actor, trip_id=trip_id, order=body.order, recipient=body.recipient,
            delivery_address=body.delivery_address,
            window_starts_at=body.window.starts_at if body.window else None,
            window_ends_at=body.window.ends_at if body.window else None,
        )
    )
    return DeliveryResponse.from_dto(dto)


@router.patch("/{trip_id}/entregas/{entrega_id}", response_model=DeliveryResponse)
async def update_delivery(
    trip_id: uuid.UUID,
    entrega_id: uuid.UUID,
    body: UpdateDeliveryRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.delivery.edit")),
) -> DeliveryResponse:
    handler = UpdateDeliveryHandler()
    dto = await handler.handle(
        UpdateDeliveryCommand(
            actor=actor, trip_id=trip_id, delivery_id=entrega_id, recipient=body.recipient,
            delivery_address=body.delivery_address,
            status=DeliveryStatus(body.status) if body.status else None,
            rejection_reason=body.rejection_reason,
        )
    )
    return DeliveryResponse.from_dto(dto)


@router.post("/{trip_id}/entregas/{entrega_id}/canhoto", response_model=ProofOfDeliveryResponse, status_code=201)
async def register_proof_of_delivery(
    trip_id: uuid.UUID,
    entrega_id: uuid.UUID,
    body: RegisterProofOfDeliveryRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.pod.create")),
) -> ProofOfDeliveryResponse:
    handler = RegisterProofOfDeliveryHandler()
    dto = await handler.handle(
        RegisterProofOfDeliveryCommand(
            actor=actor, trip_id=trip_id, delivery_id=entrega_id, signature_file_id=body.signature_file_id
        )
    )
    return ProofOfDeliveryResponse.from_dto(dto)
