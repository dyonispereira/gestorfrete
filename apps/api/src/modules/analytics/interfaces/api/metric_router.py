from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.analytics.application.commands.create_metric import CreateMetricCommand, CreateMetricHandler
from modules.analytics.application.commands.update_metric import UpdateMetricCommand, UpdateMetricHandler
from modules.analytics.application.queries.get_metric import GetMetricHandler, GetMetricQuery
from modules.analytics.application.queries.list_metrics import ListMetricsHandler, ListMetricsQuery
from modules.analytics.domain.value_objects.metric_dimensional_granularity import MetricDimensionalGranularity
from modules.analytics.domain.value_objects.metric_periodicity import MetricPeriodicity
from modules.analytics.domain.value_objects.metric_status import MetricStatus
from modules.analytics.domain.value_objects.metric_temporal_granularity import MetricTemporalGranularity
from modules.analytics.interfaces.schemas.metric_schemas import (
    CreateMetricRequest,
    MetricResponse,
    UpdateMetricRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/analytics/metrics", tags=["Metrics"])


@router.get("")
async def list_metrics(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    temporal_granularity: str | None = None,
    dimensional_granularity: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("analytics.metric.view")),
) -> dict[str, Any]:
    handler = ListMetricsHandler(get_session_factory())
    result = await handler.handle(
        ListMetricsQuery(
            actor=actor, page=page, limit=limit, search=search, temporal_granularity=temporal_granularity,
            dimensional_granularity=dimensional_granularity, status=status,
        )
    )
    return {
        "data": [MetricResponse.from_dto(m) for m in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(
    metric_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("analytics.metric.view"))
) -> MetricResponse:
    handler = GetMetricHandler(get_session_factory())
    dto = await handler.handle(GetMetricQuery(actor=actor, metric_id=metric_id))
    return MetricResponse.from_dto(dto)


@router.post("", response_model=MetricResponse, status_code=201)
async def create_metric(
    body: CreateMetricRequest, actor: AuthenticatedActor = Depends(require_permission("analytics.metric.create"))
) -> MetricResponse:
    handler = CreateMetricHandler()
    dto = await handler.handle(
        CreateMetricCommand(
            actor=actor, name=body.name, formula=body.formula,
            temporal_granularity=MetricTemporalGranularity(body.temporal_granularity),
            dimensional_granularity=MetricDimensionalGranularity(body.dimensional_granularity), unit=body.unit,
            data_sources=body.data_sources, calculation_periodicity=MetricPeriodicity(body.calculation_periodicity),
        )
    )
    return MetricResponse.from_dto(dto)


@router.patch("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: uuid.UUID, body: UpdateMetricRequest,
    actor: AuthenticatedActor = Depends(require_permission("analytics.metric.edit")),
) -> MetricResponse:
    handler = UpdateMetricHandler()
    dto = await handler.handle(
        UpdateMetricCommand(
            actor=actor, metric_id=metric_id, name=body.name, formula=body.formula, unit=body.unit,
            data_sources=body.data_sources,
            calculation_periodicity=MetricPeriodicity(body.calculation_periodicity)
            if body.calculation_periodicity else None,
            status=MetricStatus(body.status) if body.status else None,
        )
    )
    return MetricResponse.from_dto(dto)
