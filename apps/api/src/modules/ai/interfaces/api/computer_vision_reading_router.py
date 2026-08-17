from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.commands.confirm_computer_vision_reading import (
    ConfirmComputerVisionReadingCommand,
    ConfirmComputerVisionReadingHandler,
)
from modules.ai.application.commands.reject_computer_vision_reading import (
    RejectComputerVisionReadingCommand,
    RejectComputerVisionReadingHandler,
)
from modules.ai.application.queries.get_computer_vision_reading import (
    GetComputerVisionReadingHandler,
    GetComputerVisionReadingQuery,
)
from modules.ai.application.queries.list_computer_vision_readings import (
    ListComputerVisionReadingsHandler,
    ListComputerVisionReadingsQuery,
)
from modules.ai.interfaces.schemas.computer_vision_reading_schemas import (
    ComputerVisionReadingResponse,
    RejectComputerVisionReadingRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/computer-vision/readings", tags=["Computer Vision Readings"])


@router.get("")
async def list_computer_vision_readings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    reading_type: str | None = None,
    status: str | None = None,
    human_review_required: bool | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.computer_vision.view")),
) -> dict[str, Any]:
    handler = ListComputerVisionReadingsHandler(get_session_factory())
    result = await handler.handle(
        ListComputerVisionReadingsQuery(
            actor=actor, page=page, limit=limit, reading_type=reading_type, status=status,
            human_review_required=human_review_required,
        )
    )
    return {
        "data": [ComputerVisionReadingResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{reading_id}", response_model=ComputerVisionReadingResponse)
async def get_computer_vision_reading(
    reading_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.computer_vision.view"))
) -> ComputerVisionReadingResponse:
    handler = GetComputerVisionReadingHandler(get_session_factory())
    dto = await handler.handle(GetComputerVisionReadingQuery(actor=actor, reading_id=reading_id))
    return ComputerVisionReadingResponse.from_dto(dto)


@router.post("/{reading_id}/commands/confirm", response_model=ComputerVisionReadingResponse)
async def confirm_computer_vision_reading(
    reading_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("ai.computer_vision.confirm")),
) -> ComputerVisionReadingResponse:
    handler = ConfirmComputerVisionReadingHandler()
    dto = await handler.handle(ConfirmComputerVisionReadingCommand(actor=actor, reading_id=reading_id))
    return ComputerVisionReadingResponse.from_dto(dto)


@router.post("/{reading_id}/commands/reject", response_model=ComputerVisionReadingResponse)
async def reject_computer_vision_reading(
    reading_id: uuid.UUID, body: RejectComputerVisionReadingRequest,
    actor: AuthenticatedActor = Depends(require_permission("ai.computer_vision.confirm")),
) -> ComputerVisionReadingResponse:
    handler = RejectComputerVisionReadingHandler()
    dto = await handler.handle(
        RejectComputerVisionReadingCommand(actor=actor, reading_id=reading_id, reason=body.reason)
    )
    return ComputerVisionReadingResponse.from_dto(dto)
