from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.commands.create_tracking_provider import (
    CreateTrackingProviderCommand,
    CreateTrackingProviderHandler,
)
from modules.tracking.application.commands.update_tracking_provider import (
    UpdateTrackingProviderCommand,
    UpdateTrackingProviderHandler,
)
from modules.tracking.application.queries.get_tracking_provider import (
    GetTrackingProviderHandler,
    GetTrackingProviderQuery,
)
from modules.tracking.application.queries.list_tracking_providers import (
    ListTrackingProvidersHandler,
    ListTrackingProvidersQuery,
)
from modules.tracking.domain.value_objects.tracking_provider_status import TrackingProviderStatus
from modules.tracking.interfaces.schemas.tracking_provider_schemas import (
    CreateTrackingProviderRequest,
    TrackingProviderResponse,
    UpdateTrackingProviderRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tracking/providers", tags=["Tracking Providers"])


@router.get("")
async def list_providers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.provider.view")),
) -> dict[str, Any]:
    handler = ListTrackingProvidersHandler(get_session_factory())
    result = await handler.handle(
        ListTrackingProvidersQuery(actor=actor, page=page, limit=limit, search=search, status=status)
    )
    return {
        "data": [TrackingProviderResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{provider_id}", response_model=TrackingProviderResponse)
async def get_provider(
    provider_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("tracking.provider.view"))
) -> TrackingProviderResponse:
    handler = GetTrackingProviderHandler(get_session_factory())
    dto = await handler.handle(GetTrackingProviderQuery(actor=actor, provider_id=provider_id))
    return TrackingProviderResponse.from_dto(dto)


@router.post("", response_model=TrackingProviderResponse, status_code=201)
async def create_provider(
    body: CreateTrackingProviderRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.provider.create")),
) -> TrackingProviderResponse:
    handler = CreateTrackingProviderHandler()
    dto = await handler.handle(CreateTrackingProviderCommand(actor=actor, name=body.name))
    return TrackingProviderResponse.from_dto(dto)


@router.patch("/{provider_id}", response_model=TrackingProviderResponse)
async def update_provider(
    provider_id: uuid.UUID, body: UpdateTrackingProviderRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.provider.edit")),
) -> TrackingProviderResponse:
    handler = UpdateTrackingProviderHandler()
    status = TrackingProviderStatus(body.status) if body.status is not None else None
    dto = await handler.handle(
        UpdateTrackingProviderCommand(actor=actor, provider_id=provider_id, name=body.name, status=status)
    )
    return TrackingProviderResponse.from_dto(dto)
