from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.analytics.application.queries.get_consolidated_indicator import (
    GetConsolidatedIndicatorHandler,
    GetConsolidatedIndicatorQuery,
)
from modules.analytics.application.queries.list_consolidated_indicators import (
    ListConsolidatedIndicatorsHandler,
    ListConsolidatedIndicatorsQuery,
)
from modules.analytics.interfaces.schemas.consolidated_indicator_schemas import ConsolidatedIndicatorResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/analytics/indicators", tags=["Consolidated Indicators"])

# `063` — sem POST/PATCH/DELETE. Todo Indicador Consolidado nasce do processamento interno de
# `AnalyticsCalculationEngine` (D420), nunca de uma escrita direta do cliente HTTP.


@router.get("")
async def list_indicators(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    metric_id: uuid.UUID | None = None,
    dimension_type: str | None = None,
    dimension_id: uuid.UUID | None = None,
    reference_period: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("analytics.indicator.view")),
) -> dict[str, Any]:
    handler = ListConsolidatedIndicatorsHandler(get_session_factory())
    result = await handler.handle(
        ListConsolidatedIndicatorsQuery(
            actor=actor, page=page, limit=limit, metric_id=metric_id, dimension_type=dimension_type,
            dimension_id=dimension_id, reference_period=reference_period, status=status,
        )
    )
    return {
        "data": [ConsolidatedIndicatorResponse.from_dto(i) for i in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{indicator_id}", response_model=ConsolidatedIndicatorResponse)
async def get_indicator(
    indicator_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("analytics.indicator.view"))
) -> ConsolidatedIndicatorResponse:
    handler = GetConsolidatedIndicatorHandler(get_session_factory())
    dto = await handler.handle(GetConsolidatedIndicatorQuery(actor=actor, indicator_id=indicator_id))
    return ConsolidatedIndicatorResponse.from_dto(dto)
