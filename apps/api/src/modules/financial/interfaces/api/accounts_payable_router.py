from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.approve_accounts_payable import (
    ApproveAccountsPayableCommand,
    ApproveAccountsPayableHandler,
)
from modules.financial.application.commands.create_accounts_payable import (
    CreateAccountsPayableCommand,
    CreateAccountsPayableHandler,
)
from modules.financial.application.commands.delete_accounts_payable import (
    DeleteAccountsPayableCommand,
    DeleteAccountsPayableHandler,
)
from modules.financial.application.commands.pay_accounts_payable import (
    PayAccountsPayableCommand,
    PayAccountsPayableHandler,
)
from modules.financial.application.commands.reject_accounts_payable import (
    RejectAccountsPayableCommand,
    RejectAccountsPayableHandler,
)
from modules.financial.application.commands.update_accounts_payable import (
    UpdateAccountsPayableCommand,
    UpdateAccountsPayableHandler,
)
from modules.financial.application.queries.get_accounts_payable import (
    GetAccountsPayableHandler,
    GetAccountsPayableQuery,
)
from modules.financial.application.queries.list_accounts_payable import (
    ListAccountsPayableHandler,
    ListAccountsPayableQuery,
)
from modules.financial.application.queries.list_expense_allocations import (
    ListExpenseAllocationsHandler,
    ListExpenseAllocationsQuery,
)
from modules.financial.application.queries.list_expense_approvals import (
    ListExpenseApprovalsHandler,
    ListExpenseApprovalsQuery,
)
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.interfaces.schemas.accounts_payable_schemas import (
    AccountsPayableResponse,
    CreateAccountsPayableRequest,
    ExpenseAllocationResponse,
    ExpenseApprovalResponse,
    ExpenseDecisionRequest,
    PayAccountsPayableRequest,
    UpdateAccountsPayableRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/contas-pagar", tags=["Accounts Payable"])


@router.get("")
async def list_accounts_payable(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    origin: str | None = None,
    supplier_id: uuid.UUID | None = None,
    cost_center_id: uuid.UUID | None = None,
    trip_id: uuid.UUID | None = None,
    due_date__gte: date | None = None,
    due_date__lte: date | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.view")),
) -> dict[str, Any]:
    handler = ListAccountsPayableHandler(get_session_factory())
    result = await handler.handle(
        ListAccountsPayableQuery(
            actor=actor, page=page, limit=limit, status=status, origin=origin, supplier_id=supplier_id,
            cost_center_id=cost_center_id, trip_id=trip_id, due_date_from=due_date__gte, due_date_to=due_date__lte,
        )
    )
    return {
        "data": [AccountsPayableResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{accounts_payable_id}", response_model=AccountsPayableResponse)
async def get_accounts_payable(
    accounts_payable_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.view")),
) -> AccountsPayableResponse:
    handler = GetAccountsPayableHandler(get_session_factory())
    dto = await handler.handle(GetAccountsPayableQuery(actor=actor, accounts_payable_id=accounts_payable_id))
    return AccountsPayableResponse.from_dto(dto)


@router.get("/{accounts_payable_id}/aprovacoes")
async def list_expense_approvals(
    accounts_payable_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.view")),
) -> dict[str, Any]:
    handler = ListExpenseApprovalsHandler(get_session_factory())
    approvals = await handler.handle(
        ListExpenseApprovalsQuery(actor=actor, accounts_payable_id=accounts_payable_id)
    )
    items = [ExpenseApprovalResponse.from_dto(a) for a in approvals]
    return {"data": items, "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}}}


@router.get("/{accounts_payable_id}/rateios")
async def list_expense_allocations(
    accounts_payable_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.cost_allocation.view")),
) -> dict[str, Any]:
    handler = ListExpenseAllocationsHandler(get_session_factory())
    allocations = await handler.handle(
        ListExpenseAllocationsQuery(actor=actor, accounts_payable_id=accounts_payable_id)
    )
    items = [ExpenseAllocationResponse.from_dto(a) for a in allocations]
    return {"data": items, "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}}}


@router.post("", response_model=AccountsPayableResponse, status_code=201)
async def create_accounts_payable(
    body: CreateAccountsPayableRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.create")),
) -> AccountsPayableResponse:
    handler = CreateAccountsPayableHandler()
    dto = await handler.handle(
        CreateAccountsPayableCommand(
            actor=actor, supplier_id=body.supplier_id, cost_center_id=body.cost_center_id,
            origem=PayableOrigin(body.origin), trip_id=body.trip_id,
            maintenance_order_id=body.maintenance_order_id, valor=body.value, data_vencimento=body.due_date,
            chart_of_accounts_id=body.chart_of_accounts_id,
        )
    )
    return AccountsPayableResponse.from_dto(dto)


@router.patch("/{accounts_payable_id}", response_model=AccountsPayableResponse)
async def update_accounts_payable(
    accounts_payable_id: uuid.UUID,
    body: UpdateAccountsPayableRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.edit")),
) -> AccountsPayableResponse:
    handler = UpdateAccountsPayableHandler()
    dto = await handler.handle(
        UpdateAccountsPayableCommand(
            actor=actor, accounts_payable_id=accounts_payable_id, supplier_id=body.supplier_id,
            cost_center_id=body.cost_center_id, valor=body.value, data_vencimento=body.due_date,
            chart_of_accounts_id=body.chart_of_accounts_id,
        )
    )
    return AccountsPayableResponse.from_dto(dto)


@router.delete("/{accounts_payable_id}", status_code=204, response_model=None)
async def delete_accounts_payable(
    accounts_payable_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.edit")),
) -> None:
    handler = DeleteAccountsPayableHandler()
    await handler.handle(DeleteAccountsPayableCommand(actor=actor, accounts_payable_id=accounts_payable_id))


@router.post("/{accounts_payable_id}/commands/approve", response_model=AccountsPayableResponse)
async def approve_accounts_payable(
    accounts_payable_id: uuid.UUID,
    body: ExpenseDecisionRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.approve")),
) -> AccountsPayableResponse:
    handler = ApproveAccountsPayableHandler()
    dto = await handler.handle(
        ApproveAccountsPayableCommand(
            actor=actor, accounts_payable_id=accounts_payable_id, justification=body.justification
        )
    )
    return AccountsPayableResponse.from_dto(dto)


@router.post("/{accounts_payable_id}/commands/reject", response_model=AccountsPayableResponse)
async def reject_accounts_payable(
    accounts_payable_id: uuid.UUID,
    body: ExpenseDecisionRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.reject")),
) -> AccountsPayableResponse:
    handler = RejectAccountsPayableHandler()
    dto = await handler.handle(
        RejectAccountsPayableCommand(
            actor=actor, accounts_payable_id=accounts_payable_id, justification=body.justification or ""
        )
    )
    return AccountsPayableResponse.from_dto(dto)


@router.post("/{accounts_payable_id}/commands/pay", response_model=AccountsPayableResponse)
async def pay_accounts_payable(
    accounts_payable_id: uuid.UUID,
    body: PayAccountsPayableRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payable.pay")),
) -> AccountsPayableResponse:
    handler = PayAccountsPayableHandler()
    dto = await handler.handle(
        PayAccountsPayableCommand(
            actor=actor, accounts_payable_id=accounts_payable_id, bank_account_id=body.bank_account_id
        )
    )
    return AccountsPayableResponse.from_dto(dto)
