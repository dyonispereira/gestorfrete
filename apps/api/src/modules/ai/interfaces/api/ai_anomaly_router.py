from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.commands.review_anomaly import ReviewAnomalyCommand, ReviewAnomalyHandler
from modules.ai.application.queries.get_anomaly import GetAnomalyHandler, GetAnomalyQuery
from modules.ai.application.queries.list_anomalies import ListAnomaliesHandler, ListAnomaliesQuery
from modules.ai.domain.value_objects.anomaly_status import AnomalyStatus
from modules.ai.interfaces.schemas.ai_anomaly_schemas import AIAnomalyResponse, ReviewAnomalyRequest
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/anomalies", tags=["AI Anomalies"])


@router.get("")
async def list_anomalies(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    source_reading_type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.anomaly.view")),
) -> dict[str, Any]:
    handler = ListAnomaliesHandler(get_session_factory())
    result = await handler.handle(
        ListAnomaliesQuery(
            actor=actor, page=page, limit=limit, source_reading_type=source_reading_type, status=status,
        )
    )
    return {
        "data": [AIAnomalyResponse.from_dto(a) for a in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{anomaly_id}", response_model=AIAnomalyResponse)
async def get_anomaly(
    anomaly_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.anomaly.view"))
) -> AIAnomalyResponse:
    handler = GetAnomalyHandler(get_session_factory())
    dto = await handler.handle(GetAnomalyQuery(actor=actor, anomaly_id=anomaly_id))
    return AIAnomalyResponse.from_dto(dto)


@router.post("/{anomaly_id}/commands/review", response_model=AIAnomalyResponse)
async def review_anomaly(
    anomaly_id: uuid.UUID, body: ReviewAnomalyRequest,
    actor: AuthenticatedActor = Depends(require_permission("ai.anomaly.review")),
) -> AIAnomalyResponse:
    handler = ReviewAnomalyHandler()
    dto = await handler.handle(
        ReviewAnomalyCommand(
            actor=actor, anomaly_id=anomaly_id, resolution=AnomalyStatus(body.resolution), notes=body.notes,
        )
    )
    return AIAnomalyResponse.from_dto(dto)
