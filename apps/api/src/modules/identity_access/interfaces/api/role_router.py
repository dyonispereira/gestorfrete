from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.application.commands.create_role import CreateRoleCommand, CreateRoleHandler
from modules.identity_access.application.commands.delete_role import DeleteRoleCommand, DeleteRoleHandler
from modules.identity_access.application.commands.update_role import UpdateRoleCommand, UpdateRoleHandler
from modules.identity_access.application.queries.get_role import GetRoleHandler, GetRoleQuery
from modules.identity_access.application.queries.list_roles import ListRolesHandler, ListRolesQuery
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.identity_access.interfaces.schemas.role_schemas import (
    CreateRoleRequest,
    RoleResponse,
    UpdateRoleRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("")
async def list_roles(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.role.view")),
) -> dict[str, Any]:
    handler = ListRolesHandler(get_session_factory())
    result = await handler.handle(ListRolesQuery(actor=actor, page=page, limit=limit, search=search))
    return {
        "data": [RoleResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.role.view")),
) -> RoleResponse:
    handler = GetRoleHandler(get_session_factory())
    dto = await handler.handle(GetRoleQuery(actor=actor, role_id=role_id))
    return RoleResponse.from_dto(dto)


@router.post("", response_model=RoleResponse, status_code=201)
async def create_role(
    body: CreateRoleRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.role.create")),
) -> RoleResponse:
    handler = CreateRoleHandler()
    dto = await handler.handle(
        CreateRoleCommand(actor=actor, nome=body.nome, descricao=body.descricao, permission_codes=body.permissions)
    )
    return RoleResponse.from_dto(dto)


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    body: UpdateRoleRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.role.edit")),
) -> RoleResponse:
    handler = UpdateRoleHandler()
    dto = await handler.handle(
        UpdateRoleCommand(
            actor=actor, role_id=role_id, nome=body.nome, descricao=body.descricao, permission_codes=body.permissions
        )
    )
    return RoleResponse.from_dto(dto)


@router.delete("/{role_id}", status_code=204, response_model=None)
async def delete_role(
    role_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.role.delete")),
) -> None:
    handler = DeleteRoleHandler()
    await handler.handle(DeleteRoleCommand(actor=actor, role_id=role_id))
