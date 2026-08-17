from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.application.commands.create_employee import CreateEmployeeCommand, CreateEmployeeHandler
from modules.identity_access.application.commands.deactivate_employee import (
    DeactivateEmployeeCommand,
    DeactivateEmployeeHandler,
)
from modules.identity_access.application.commands.update_employee import UpdateEmployeeCommand, UpdateEmployeeHandler
from modules.identity_access.application.queries.get_employee import GetEmployeeHandler, GetEmployeeQuery
from modules.identity_access.application.queries.list_employees import ListEmployeesHandler, ListEmployeesQuery
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.identity_access.interfaces.schemas.employee_schemas import (
    CreateEmployeeRequest,
    EmployeeResponse,
    UpdateEmployeeRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
async def list_employees(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.employee.view")),
) -> dict[str, Any]:
    handler = ListEmployeesHandler(get_session_factory())
    result = await handler.handle(
        ListEmployeesQuery(actor=actor, page=page, limit=limit, status=status, search=search)
    )
    return {
        "data": [EmployeeResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.employee.view")),
) -> EmployeeResponse:
    handler = GetEmployeeHandler(get_session_factory())
    dto = await handler.handle(GetEmployeeQuery(actor=actor, employee_id=employee_id))
    return EmployeeResponse.from_dto(dto)


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    body: CreateEmployeeRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.employee.create")),
) -> EmployeeResponse:
    handler = CreateEmployeeHandler()
    dto = await handler.handle(
        CreateEmployeeCommand(actor=actor, nome=body.nome, cargo=body.cargo, data_admissao=body.hired_at)
    )
    return EmployeeResponse.from_dto(dto)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: uuid.UUID,
    body: UpdateEmployeeRequest,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.employee.edit")),
) -> EmployeeResponse:
    handler = UpdateEmployeeHandler()
    dto = await handler.handle(
        UpdateEmployeeCommand(
            actor=actor, employee_id=employee_id, nome=body.nome, cargo=body.cargo, data_admissao=body.hired_at
        )
    )
    return EmployeeResponse.from_dto(dto)


@router.delete("/{employee_id}", status_code=204, response_model=None)
async def deactivate_employee(
    employee_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("identity_access.employee.delete")),
) -> None:
    handler = DeactivateEmployeeHandler()
    await handler.handle(DeactivateEmployeeCommand(actor=actor, employee_id=employee_id))
