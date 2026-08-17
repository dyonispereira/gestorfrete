from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.create_chart_of_accounts import (
    CreateChartOfAccountsCommand,
    CreateChartOfAccountsHandler,
)
from modules.financial.application.commands.delete_chart_of_accounts import (
    DeleteChartOfAccountsCommand,
    DeleteChartOfAccountsHandler,
)
from modules.financial.application.commands.update_chart_of_accounts import (
    UpdateChartOfAccountsCommand,
    UpdateChartOfAccountsHandler,
)
from modules.financial.application.queries.get_chart_of_accounts import (
    GetChartOfAccountsHandler,
    GetChartOfAccountsQuery,
)
from modules.financial.application.queries.list_chart_of_accounts import (
    ListChartOfAccountsHandler,
    ListChartOfAccountsQuery,
)
from modules.financial.domain.value_objects.chart_of_accounts_status import ChartOfAccountsStatus
from modules.financial.domain.value_objects.chart_of_accounts_type import ChartOfAccountsType
from modules.financial.interfaces.schemas.chart_of_accounts_schemas import (
    ChartOfAccountsResponse,
    CreateChartOfAccountsRequest,
    UpdateChartOfAccountsRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/plano-contas", tags=["Chart of Accounts"])


@router.get("")
async def list_chart_of_accounts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    type: str | None = None,
    parent_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.chart_of_accounts.view")),
) -> dict[str, Any]:
    handler = ListChartOfAccountsHandler(get_session_factory())
    result = await handler.handle(
        ListChartOfAccountsQuery(
            actor=actor, page=page, limit=limit, search=search, tipo=type, parent_id=parent_id, status=status
        )
    )
    return {
        "data": [ChartOfAccountsResponse.from_dto(a) for a in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{chart_of_accounts_id}", response_model=ChartOfAccountsResponse)
async def get_chart_of_accounts(
    chart_of_accounts_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.chart_of_accounts.view")),
) -> ChartOfAccountsResponse:
    handler = GetChartOfAccountsHandler(get_session_factory())
    dto = await handler.handle(GetChartOfAccountsQuery(actor=actor, chart_of_accounts_id=chart_of_accounts_id))
    return ChartOfAccountsResponse.from_dto(dto)


@router.post("", response_model=ChartOfAccountsResponse, status_code=201)
async def create_chart_of_accounts(
    body: CreateChartOfAccountsRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.chart_of_accounts.create")),
) -> ChartOfAccountsResponse:
    handler = CreateChartOfAccountsHandler()
    dto = await handler.handle(
        CreateChartOfAccountsCommand(
            actor=actor, account_code=body.account_code, name=body.name,
            tipo=ChartOfAccountsType(body.type), parent_id=body.parent_id,
        )
    )
    return ChartOfAccountsResponse.from_dto(dto)


@router.patch("/{chart_of_accounts_id}", response_model=ChartOfAccountsResponse)
async def update_chart_of_accounts(
    chart_of_accounts_id: uuid.UUID,
    body: UpdateChartOfAccountsRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.chart_of_accounts.edit")),
) -> ChartOfAccountsResponse:
    handler = UpdateChartOfAccountsHandler()
    dto = await handler.handle(
        UpdateChartOfAccountsCommand(
            actor=actor, chart_of_accounts_id=chart_of_accounts_id, name=body.name, parent_id=body.parent_id,
            status=ChartOfAccountsStatus(body.status) if body.status else None,
        )
    )
    return ChartOfAccountsResponse.from_dto(dto)


@router.delete("/{chart_of_accounts_id}", status_code=204, response_model=None)
async def delete_chart_of_accounts(
    chart_of_accounts_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.chart_of_accounts.delete")),
) -> None:
    handler = DeleteChartOfAccountsHandler()
    await handler.handle(DeleteChartOfAccountsCommand(actor=actor, chart_of_accounts_id=chart_of_accounts_id))
