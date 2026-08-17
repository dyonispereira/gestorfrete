from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.identity_access.interfaces.dependencies.authorization import (
    get_authorization_service,
    require_permission,
)
from modules.reporting.application.commands.create_dashboard import CreateDashboardCommand, CreateDashboardHandler
from modules.reporting.application.commands.delete_dashboard import DeleteDashboardCommand, DeleteDashboardHandler
from modules.reporting.application.commands.share_dashboard import ShareDashboardCommand, ShareDashboardHandler
from modules.reporting.application.commands.update_dashboard import UpdateDashboardCommand, UpdateDashboardHandler
from modules.reporting.application.queries.get_dashboard import GetDashboardHandler, GetDashboardQuery
from modules.reporting.application.queries.list_dashboards import ListDashboardsHandler, ListDashboardsQuery
from modules.reporting.domain.value_objects.dashboard_sharing import DashboardSharing
from modules.reporting.interfaces.schemas.dashboard_schemas import (
    CreateDashboardRequest,
    DashboardResponse,
    ShareDashboardRequest,
    UpdateDashboardRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/reporting/dashboards", tags=["Dashboards"])


@router.get("")
async def list_dashboards(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.view_own")),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> dict[str, Any]:
    codes = await authz.get_permission_codes(actor)
    include_shared = "reporting.dashboard.view_shared" in codes
    handler = ListDashboardsHandler(get_session_factory())
    result = await handler.handle(
        ListDashboardsQuery(
            actor=actor, page=page, limit=limit, search=search, status=status, include_shared=include_shared
        )
    )
    return {
        "data": [DashboardResponse.from_dto(d) for d in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.view_own")),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DashboardResponse:
    codes = await authz.get_permission_codes(actor)
    has_view_shared = "reporting.dashboard.view_shared" in codes
    handler = GetDashboardHandler(get_session_factory())
    dto = await handler.handle(
        GetDashboardQuery(actor=actor, dashboard_id=dashboard_id, has_view_shared_permission=has_view_shared)
    )
    return DashboardResponse.from_dto(dto)


@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    body: CreateDashboardRequest, actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.create"))
) -> DashboardResponse:
    handler = CreateDashboardHandler()
    dto = await handler.handle(
        CreateDashboardCommand(
            actor=actor, name=body.name, layout=body.layout, widgets=body.widgets, filters=body.filters,
            preferences=body.preferences,
        )
    )
    return DashboardResponse.from_dto(dto)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID, body: UpdateDashboardRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.edit_own")),
) -> DashboardResponse:
    handler = UpdateDashboardHandler()
    dto = await handler.handle(
        UpdateDashboardCommand(
            actor=actor, dashboard_id=dashboard_id, name=body.name, layout=body.layout, widgets=body.widgets,
            filters=body.filters, preferences=body.preferences, status=body.status,
        )
    )
    return DashboardResponse.from_dto(dto)


@router.delete("/{dashboard_id}", status_code=204, response_model=None)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.delete_own")),
) -> None:
    handler = DeleteDashboardHandler()
    await handler.handle(DeleteDashboardCommand(actor=actor, dashboard_id=dashboard_id))


@router.post("/{dashboard_id}/commands/share", response_model=DashboardResponse)
async def share_dashboard(
    dashboard_id: uuid.UUID, body: ShareDashboardRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.dashboard.share")),
) -> DashboardResponse:
    handler = ShareDashboardHandler()
    dto = await handler.handle(
        ShareDashboardCommand(actor=actor, dashboard_id=dashboard_id, sharing=DashboardSharing(body.sharing))
    )
    return DashboardResponse.from_dto(dto)
