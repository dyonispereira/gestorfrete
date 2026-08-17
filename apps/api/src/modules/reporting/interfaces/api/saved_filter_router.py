from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.reporting.application.commands.create_saved_filter import (
    CreateSavedFilterCommand,
    CreateSavedFilterHandler,
)
from modules.reporting.application.commands.delete_saved_filter import (
    DeleteSavedFilterCommand,
    DeleteSavedFilterHandler,
)
from modules.reporting.application.commands.update_saved_filter import (
    UpdateSavedFilterCommand,
    UpdateSavedFilterHandler,
)
from modules.reporting.application.queries.get_saved_filter import GetSavedFilterHandler, GetSavedFilterQuery
from modules.reporting.application.queries.list_saved_filters import ListSavedFiltersHandler, ListSavedFiltersQuery
from modules.reporting.interfaces.schemas.saved_filter_schemas import (
    CreateSavedFilterRequest,
    SavedFilterResponse,
    UpdateSavedFilterRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/reporting/saved-filters", tags=["Saved Filters"])


@router.get("")
async def list_saved_filters(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_filter.view_own")),
) -> dict[str, Any]:
    handler = ListSavedFiltersHandler(get_session_factory())
    result = await handler.handle(
        ListSavedFiltersQuery(actor=actor, page=page, limit=limit, search=search, status=status)
    )
    return {
        "data": [SavedFilterResponse.from_dto(f) for f in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{saved_filter_id}", response_model=SavedFilterResponse)
async def get_saved_filter(
    saved_filter_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_filter.view_own")),
) -> SavedFilterResponse:
    handler = GetSavedFilterHandler(get_session_factory())
    dto = await handler.handle(GetSavedFilterQuery(actor=actor, saved_filter_id=saved_filter_id))
    return SavedFilterResponse.from_dto(dto)


@router.post("", response_model=SavedFilterResponse, status_code=201)
async def create_saved_filter(
    body: CreateSavedFilterRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_filter.create")),
) -> SavedFilterResponse:
    handler = CreateSavedFilterHandler()
    dto = await handler.handle(CreateSavedFilterCommand(actor=actor, name=body.name, criteria=body.criteria))
    return SavedFilterResponse.from_dto(dto)


@router.patch("/{saved_filter_id}", response_model=SavedFilterResponse)
async def update_saved_filter(
    saved_filter_id: uuid.UUID, body: UpdateSavedFilterRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_filter.edit_own")),
) -> SavedFilterResponse:
    handler = UpdateSavedFilterHandler()
    dto = await handler.handle(
        UpdateSavedFilterCommand(
            actor=actor, saved_filter_id=saved_filter_id, name=body.name, criteria=body.criteria,
            status=body.status,
        )
    )
    return SavedFilterResponse.from_dto(dto)


@router.delete("/{saved_filter_id}", status_code=204, response_model=None)
async def delete_saved_filter(
    saved_filter_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_filter.delete_own")),
) -> None:
    handler = DeleteSavedFilterHandler()
    await handler.handle(DeleteSavedFilterCommand(actor=actor, saved_filter_id=saved_filter_id))
