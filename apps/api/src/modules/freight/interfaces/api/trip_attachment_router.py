from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from modules.freight.application.commands.create_trip_attachment import (
    CreateTripAttachmentCommand,
    CreateTripAttachmentHandler,
)
from modules.freight.application.commands.delete_trip_attachment import (
    DeleteTripAttachmentCommand,
    DeleteTripAttachmentHandler,
)
from modules.freight.application.queries.list_trip_attachments import (
    ListTripAttachmentsHandler,
    ListTripAttachmentsQuery,
)
from modules.freight.interfaces.schemas.attachment_schemas import AttachmentResponse, CreateAttachmentRequest
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Attachments"])


@router.get("/{trip_id}/attachments")
async def list_trip_attachments(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.trip.view"))
) -> dict[str, Any]:
    handler = ListTripAttachmentsHandler(get_session_factory())
    items = await handler.handle(ListTripAttachmentsQuery(actor=actor, trip_id=trip_id))
    responses = [AttachmentResponse.from_entity(a) for a in items]
    return {"data": responses, "meta": {"pagination": {"page": 1, "limit": len(responses), "total": len(responses)}}}


@router.post("/{trip_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def create_trip_attachment(
    trip_id: uuid.UUID, body: CreateAttachmentRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
) -> AttachmentResponse:
    handler = CreateTripAttachmentHandler()
    attachment = await handler.handle(
        CreateTripAttachmentCommand(
            actor=actor, trip_id=trip_id, attachment_type=body.attachment_type, file_id=body.file_id,
            description=body.description,
        )
    )
    return AttachmentResponse.from_entity(attachment)


@router.delete("/{trip_id}/attachments/{attachment_id}", status_code=204, response_model=None)
async def delete_trip_attachment(
    trip_id: uuid.UUID, attachment_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.edit")),
) -> None:
    handler = DeleteTripAttachmentHandler()
    await handler.handle(DeleteTripAttachmentCommand(actor=actor, trip_id=trip_id, attachment_id=attachment_id))
