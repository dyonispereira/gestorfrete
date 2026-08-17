from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.analytics.application.commands.create_analytics_cube import (
    CreateAnalyticsCubeCommand,
    CreateAnalyticsCubeHandler,
)
from modules.analytics.application.commands.update_analytics_cube import (
    UpdateAnalyticsCubeCommand,
    UpdateAnalyticsCubeHandler,
)
from modules.analytics.application.queries.get_analytics_cube import GetAnalyticsCubeHandler, GetAnalyticsCubeQuery
from modules.analytics.application.queries.list_analytics_cubes import (
    ListAnalyticsCubesHandler,
    ListAnalyticsCubesQuery,
)
from modules.analytics.interfaces.schemas.analytics_cube_schemas import (
    AnalyticsCubeResponse,
    CreateAnalyticsCubeRequest,
    UpdateAnalyticsCubeRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/analytics/cubes", tags=["Analytics Cubes"])


@router.get("")
async def list_cubes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("analytics.cube.view")),
) -> dict[str, Any]:
    handler = ListAnalyticsCubesHandler(get_session_factory())
    result = await handler.handle(
        ListAnalyticsCubesQuery(actor=actor, page=page, limit=limit, search=search, status=status)
    )
    return {
        "data": [AnalyticsCubeResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{cube_id}", response_model=AnalyticsCubeResponse)
async def get_cube(
    cube_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("analytics.cube.view"))
) -> AnalyticsCubeResponse:
    handler = GetAnalyticsCubeHandler(get_session_factory())
    dto = await handler.handle(GetAnalyticsCubeQuery(actor=actor, cube_id=cube_id))
    return AnalyticsCubeResponse.from_dto(dto)


@router.post("", response_model=AnalyticsCubeResponse, status_code=201)
async def create_cube(
    body: CreateAnalyticsCubeRequest, actor: AuthenticatedActor = Depends(require_permission("analytics.cube.create"))
) -> AnalyticsCubeResponse:
    handler = CreateAnalyticsCubeHandler()
    dto = await handler.handle(
        CreateAnalyticsCubeCommand(
            actor=actor, name=body.name, dimensions=body.dimensions, metric_ids=body.metric_ids
        )
    )
    return AnalyticsCubeResponse.from_dto(dto)


@router.patch("/{cube_id}", response_model=AnalyticsCubeResponse)
async def update_cube(
    cube_id: uuid.UUID, body: UpdateAnalyticsCubeRequest,
    actor: AuthenticatedActor = Depends(require_permission("analytics.cube.edit")),
) -> AnalyticsCubeResponse:
    handler = UpdateAnalyticsCubeHandler()
    dto = await handler.handle(
        UpdateAnalyticsCubeCommand(
            actor=actor, cube_id=cube_id, dimensions=body.dimensions, metric_ids=body.metric_ids,
            status=body.status,
        )
    )
    return AnalyticsCubeResponse.from_dto(dto)
