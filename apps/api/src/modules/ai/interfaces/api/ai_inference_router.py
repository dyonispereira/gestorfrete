from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.queries.get_inference import GetInferenceHandler, GetInferenceQuery
from modules.ai.application.queries.list_inferences import ListInferencesHandler, ListInferencesQuery
from modules.ai.interfaces.schemas.ai_inference_schemas import AIInferenceResponse
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.identity_access.interfaces.dependencies.authorization import (
    get_authorization_service,
    require_permission,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/inferences", tags=["AI Inferences"])


@router.get("")
async def list_inferences(
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    model_id: uuid.UUID | None = None,
    status: str | None = None,
    origin: str | None = None,
    started_at__gte: datetime | None = None,
    started_at__lte: datetime | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.inference.view")),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> dict[str, Any]:
    held = await authz.get_permission_codes(actor)
    handler = ListInferencesHandler(get_session_factory())
    result = await handler.handle(
        ListInferencesQuery(
            actor=actor, held_permissions=held, cursor=cursor, limit=limit, model_id=model_id, status=status,
            origin=origin, started_at_from=started_at__gte, started_at_to=started_at__lte,
        )
    )
    return {
        "data": [AIInferenceResponse.from_dto(i) for i in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.get("/{inference_id}", response_model=AIInferenceResponse)
async def get_inference(
    inference_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("ai.inference.view")),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AIInferenceResponse:
    held = await authz.get_permission_codes(actor)
    handler = GetInferenceHandler(get_session_factory())
    dto = await handler.handle(GetInferenceQuery(actor=actor, inference_id=inference_id, held_permissions=held))
    return AIInferenceResponse.from_dto(dto)
