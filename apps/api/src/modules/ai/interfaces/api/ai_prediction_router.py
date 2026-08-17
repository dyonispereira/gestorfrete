from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.queries.get_prediction import GetPredictionHandler, GetPredictionQuery
from modules.ai.application.queries.list_predictions import ListPredictionsHandler, ListPredictionsQuery
from modules.ai.interfaces.schemas.ai_prediction_schemas import AIPredictionResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/predictions", tags=["AI Predictions"])


@router.get("")
async def list_predictions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    target_entity_type: str | None = None,
    target_entity_id: uuid.UUID | None = None,
    include_expired: bool = False,
    actor: AuthenticatedActor = Depends(require_permission("ai.prediction.view")),
) -> dict[str, Any]:
    handler = ListPredictionsHandler(get_session_factory())
    result = await handler.handle(
        ListPredictionsQuery(
            actor=actor, page=page, limit=limit, category=category, target_entity_type=target_entity_type,
            target_entity_id=target_entity_id, include_expired=include_expired,
        )
    )
    return {
        "data": [AIPredictionResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{prediction_id}", response_model=AIPredictionResponse)
async def get_prediction(
    prediction_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.prediction.view"))
) -> AIPredictionResponse:
    handler = GetPredictionHandler(get_session_factory())
    dto = await handler.handle(GetPredictionQuery(actor=actor, prediction_id=prediction_id))
    return AIPredictionResponse.from_dto(dto)
