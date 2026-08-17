from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.create_cost_center import (
    CreateCostCenterCommand,
    CreateCostCenterHandler,
)
from modules.financial.application.commands.update_cost_center import (
    UpdateCostCenterCommand,
    UpdateCostCenterHandler,
)
from modules.financial.application.queries.get_cost_center import GetCostCenterHandler, GetCostCenterQuery
from modules.financial.application.queries.list_cost_centers import ListCostCentersHandler, ListCostCentersQuery
from modules.financial.domain.value_objects.cost_center_status import CostCenterStatus
from modules.financial.interfaces.schemas.cost_center_schemas import (
    CostCenterResponse,
    CreateCostCenterRequest,
    UpdateCostCenterRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/cost-centers", tags=["Cost Centers"])


@router.get("")
async def list_cost_centers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    branch_id: uuid.UUID | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.cost_center.view")),
) -> dict[str, Any]:
    handler = ListCostCentersHandler(get_session_factory())
    result = await handler.handle(
        ListCostCentersQuery(actor=actor, page=page, limit=limit, status=status, branch_id=branch_id, search=search)
    )
    return {
        "data": [CostCenterResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{cost_center_id}", response_model=CostCenterResponse)
async def get_cost_center(
    cost_center_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.cost_center.view")),
) -> CostCenterResponse:
    handler = GetCostCenterHandler(get_session_factory())
    dto = await handler.handle(GetCostCenterQuery(actor=actor, cost_center_id=cost_center_id))
    return CostCenterResponse.from_dto(dto)


@router.post("", response_model=CostCenterResponse, status_code=201)
async def create_cost_center(
    body: CreateCostCenterRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.cost_center.create")),
) -> CostCenterResponse:
    handler = CreateCostCenterHandler()
    dto = await handler.handle(
        CreateCostCenterCommand(
            actor=actor, codigo_contabil=body.accounting_code, nome=body.nome, filial_id=body.branch_id
        )
    )
    return CostCenterResponse.from_dto(dto)


@router.patch("/{cost_center_id}", response_model=CostCenterResponse)
async def update_cost_center(
    cost_center_id: uuid.UUID,
    body: UpdateCostCenterRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.cost_center.edit")),
) -> CostCenterResponse:
    handler = UpdateCostCenterHandler()
    dto = await handler.handle(
        UpdateCostCenterCommand(
            actor=actor,
            cost_center_id=cost_center_id,
            nome=body.nome,
            filial_id=body.branch_id,
            status=CostCenterStatus(body.status) if body.status else None,
        )
    )
    return CostCenterResponse.from_dto(dto)


# Sem DELETE — RBAC_MATRIX.md não tem financial.cost_center.delete (D216, COST_CENTER_IMPLEMENTATION.md)
