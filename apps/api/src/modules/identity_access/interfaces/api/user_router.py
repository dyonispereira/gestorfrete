from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.application.commands.create_user import CreateUserCommand, CreateUserHandler
from modules.identity_access.application.commands.deactivate_user import (
    DeactivateUserCommand,
    DeactivateUserHandler,
)
from modules.identity_access.application.commands.update_user import UpdateUserCommand, UpdateUserHandler
from modules.identity_access.application.queries.get_user import GetUserHandler, GetUserQuery
from modules.identity_access.application.queries.list_users import ListUsersHandler, ListUsersQuery
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.identity_access.interfaces.schemas.user_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    role: uuid.UUID | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.user.view")),
) -> dict[str, Any]:
    handler = ListUsersHandler(get_session_factory())
    result = await handler.handle(
        ListUsersQuery(actor=actor, page=page, limit=limit, status=status, role_id=role, search=search)
    )
    return {
        "data": [UserResponse.from_dto(u) for u in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.user.view")),
) -> UserResponse:
    handler = GetUserHandler(get_session_factory())
    dto = await handler.handle(GetUserQuery(actor=actor, user_id=user_id))
    return UserResponse.from_dto(dto)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: CreateUserRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.user.create")),
) -> UserResponse:
    handler = CreateUserHandler()
    dto = await handler.handle(
        CreateUserCommand(
            actor=actor,
            nome=body.nome,
            email=body.email,
            password=body.password,
            driver_id=body.driver_id,
            employee_id=body.employee_id,
            role_ids=frozenset(body.role_ids),
        )
    )
    return UserResponse.from_dto(dto)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.user.edit")),
) -> UserResponse:
    handler = UpdateUserHandler()
    dto = await handler.handle(
        UpdateUserCommand(
            actor=actor,
            user_id=user_id,
            nome=body.nome,
            email=body.email,
            role_ids=frozenset(body.role_ids) if body.role_ids is not None else None,
        )
    )
    return UserResponse.from_dto(dto)


@router.delete("/{user_id}", status_code=204, response_model=None)
async def deactivate_user(
    user_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.user.deactivate")),
) -> None:
    handler = DeactivateUserHandler()
    await handler.handle(DeactivateUserCommand(actor=actor, user_id=user_id))
