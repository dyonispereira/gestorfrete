from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.queries.get_classification import GetClassificationHandler, GetClassificationQuery
from modules.ai.application.queries.list_classifications import (
    ListClassificationsHandler,
    ListClassificationsQuery,
)
from modules.ai.interfaces.schemas.ai_classification_schemas import AIClassificationResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/classifications", tags=["AI Classifications"])


@router.get("")
async def list_classifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    classification_type: str | None = None,
    target_entity_type: str | None = None,
    target_entity_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.classification.view")),
) -> dict[str, Any]:
    handler = ListClassificationsHandler(get_session_factory())
    result = await handler.handle(
        ListClassificationsQuery(
            actor=actor, page=page, limit=limit, classification_type=classification_type,
            target_entity_type=target_entity_type, target_entity_id=target_entity_id,
        )
    )
    return {
        "data": [AIClassificationResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{classification_id}", response_model=AIClassificationResponse)
async def get_classification(
    classification_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("ai.classification.view")),
) -> AIClassificationResponse:
    handler = GetClassificationHandler(get_session_factory())
    dto = await handler.handle(GetClassificationQuery(actor=actor, classification_id=classification_id))
    return AIClassificationResponse.from_dto(dto)
