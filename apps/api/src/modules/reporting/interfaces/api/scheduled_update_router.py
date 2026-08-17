from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.reporting.application.commands.create_scheduled_update import (
    CreateScheduledUpdateCommand,
    CreateScheduledUpdateHandler,
)
from modules.reporting.application.commands.update_scheduled_update import (
    UpdateScheduledUpdateCommand,
    UpdateScheduledUpdateHandler,
)
from modules.reporting.application.queries.get_scheduled_update import (
    GetScheduledUpdateHandler,
    GetScheduledUpdateQuery,
)
from modules.reporting.application.queries.list_scheduled_updates import (
    ListScheduledUpdatesHandler,
    ListScheduledUpdatesQuery,
)
from modules.reporting.interfaces.schemas.scheduled_update_schemas import (
    CreateScheduledUpdateRequest,
    ScheduledUpdateResponse,
    UpdateScheduledUpdateRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/reporting/scheduled-updates", tags=["Scheduled Updates"])


@router.get("")
async def list_scheduled_updates(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    metric_id: uuid.UUID | None = None,
    cube_id: uuid.UUID | None = None,
    mode: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("reporting.scheduled_update.view")),
) -> dict[str, Any]:
    handler = ListScheduledUpdatesHandler(get_session_factory())
    result = await handler.handle(
        ListScheduledUpdatesQuery(
            actor=actor, page=page, limit=limit, metric_id=metric_id, cube_id=cube_id, mode=mode, status=status
        )
    )
    return {
        "data": [ScheduledUpdateResponse.from_dto(s) for s in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{scheduled_update_id}", response_model=ScheduledUpdateResponse)
async def get_scheduled_update(
    scheduled_update_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.scheduled_update.view")),
) -> ScheduledUpdateResponse:
    handler = GetScheduledUpdateHandler(get_session_factory())
    dto = await handler.handle(GetScheduledUpdateQuery(actor=actor, scheduled_update_id=scheduled_update_id))
    return ScheduledUpdateResponse.from_dto(dto)


@router.post("", response_model=ScheduledUpdateResponse, status_code=201)
async def create_scheduled_update(
    body: CreateScheduledUpdateRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.scheduled_update.create")),
) -> ScheduledUpdateResponse:
    handler = CreateScheduledUpdateHandler()
    dto = await handler.handle(
        CreateScheduledUpdateCommand(
            actor=actor, metric_id=body.metric_id, cube_id=body.cube_id, mode=body.mode,
        )
    )
    return ScheduledUpdateResponse.from_dto(dto)


@router.patch("/{scheduled_update_id}", response_model=ScheduledUpdateResponse)
async def update_scheduled_update(
    scheduled_update_id: uuid.UUID, body: UpdateScheduledUpdateRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.scheduled_update.edit")),
) -> ScheduledUpdateResponse:
    handler = UpdateScheduledUpdateHandler()
    dto = await handler.handle(
        UpdateScheduledUpdateCommand(
            actor=actor, scheduled_update_id=scheduled_update_id, mode=body.mode, status=body.status,
        )
    )
    return ScheduledUpdateResponse.from_dto(dto)
