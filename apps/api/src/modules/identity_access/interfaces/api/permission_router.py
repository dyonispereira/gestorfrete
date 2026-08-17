from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.application.queries.list_permissions import (
    GetPermissionHandler,
    GetPermissionQuery,
    ListPermissionsHandler,
    ListPermissionsQuery,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.identity_access.interfaces.schemas.permission_schemas import PermissionResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("")
async def list_permissions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    module: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.permission.view")),
) -> dict[str, Any]:
    handler = ListPermissionsHandler(get_session_factory())
    result = await handler.handle(
        ListPermissionsQuery(actor=actor, page=page, limit=limit, module=module, search=search)
    )
    return {
        "data": [PermissionResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.permission.view")),
) -> PermissionResponse:
    handler = GetPermissionHandler(get_session_factory())
    dto = await handler.handle(GetPermissionQuery(actor=actor, permission_id=permission_id))
    return PermissionResponse.from_dto(dto)
