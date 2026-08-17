from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.commands.create_ai_feedback import CreateAIFeedbackCommand, CreateAIFeedbackHandler
from modules.ai.application.commands.update_ai_feedback import UpdateAIFeedbackCommand, UpdateAIFeedbackHandler
from modules.ai.application.queries.get_ai_feedback import GetAIFeedbackHandler, GetAIFeedbackQuery
from modules.ai.application.queries.list_ai_feedback import ListAIFeedbackHandler, ListAIFeedbackQuery
from modules.ai.domain.value_objects.feedback_output_type import FeedbackOutputType
from modules.ai.domain.value_objects.feedback_result import FeedbackResult
from modules.ai.interfaces.schemas.ai_feedback_schemas import (
    AIFeedbackResponse,
    CreateAIFeedbackRequest,
    UpdateAIFeedbackRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/feedback", tags=["AI Feedback"])


@router.get("")
async def list_ai_feedback(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    output_type: str | None = None,
    output_id: uuid.UUID | None = None,
    result: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.feedback.view")),
) -> dict[str, Any]:
    handler = ListAIFeedbackHandler(get_session_factory())
    query_result = await handler.handle(
        ListAIFeedbackQuery(
            actor=actor, page=page, limit=limit, output_type=output_type, output_id=output_id, result=result,
        )
    )
    return {
        "data": [AIFeedbackResponse.from_dto(f) for f in query_result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": query_result.total}},
    }


@router.get("/{feedback_id}", response_model=AIFeedbackResponse)
async def get_ai_feedback(
    feedback_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.feedback.view"))
) -> AIFeedbackResponse:
    handler = GetAIFeedbackHandler(get_session_factory())
    dto = await handler.handle(GetAIFeedbackQuery(actor=actor, feedback_id=feedback_id))
    return AIFeedbackResponse.from_dto(dto)


@router.post("", response_model=AIFeedbackResponse, status_code=201)
async def create_ai_feedback(
    body: CreateAIFeedbackRequest, actor: AuthenticatedActor = Depends(require_permission("ai.feedback.create"))
) -> AIFeedbackResponse:
    handler = CreateAIFeedbackHandler()
    dto = await handler.handle(
        CreateAIFeedbackCommand(
            actor=actor, output_type=FeedbackOutputType(body.output_type), output_id=body.output_id,
            result=FeedbackResult(body.result), justification=body.justification,
            actual_result=body.actual_result,
        )
    )
    return AIFeedbackResponse.from_dto(dto)


@router.patch("/{feedback_id}", response_model=AIFeedbackResponse)
async def update_ai_feedback(
    feedback_id: uuid.UUID, body: UpdateAIFeedbackRequest,
    actor: AuthenticatedActor = Depends(require_permission("ai.feedback.create")),
) -> AIFeedbackResponse:
    handler = UpdateAIFeedbackHandler()
    dto = await handler.handle(
        UpdateAIFeedbackCommand(actor=actor, feedback_id=feedback_id, actual_result=body.actual_result)
    )
    return AIFeedbackResponse.from_dto(dto)
