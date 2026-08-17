from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.create_bank_account import (
    CreateBankAccountCommand,
    CreateBankAccountHandler,
)
from modules.financial.application.commands.delete_bank_account import (
    DeleteBankAccountCommand,
    DeleteBankAccountHandler,
)
from modules.financial.application.commands.update_bank_account import (
    UpdateBankAccountCommand,
    UpdateBankAccountHandler,
)
from modules.financial.application.queries.get_bank_account import GetBankAccountHandler, GetBankAccountQuery
from modules.financial.application.queries.get_bank_account_balance import (
    GetBankAccountBalanceHandler,
    GetBankAccountBalanceQuery,
)
from modules.financial.application.queries.list_bank_accounts import ListBankAccountsHandler, ListBankAccountsQuery
from modules.financial.domain.value_objects.bank_account_status import BankAccountStatus
from modules.financial.domain.value_objects.bank_account_type import BankAccountType
from modules.financial.interfaces.schemas.bank_account_schemas import (
    BankAccountBalanceResponse,
    BankAccountResponse,
    CreateBankAccountRequest,
    UpdateBankAccountRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/contas-bancarias", tags=["Bank Accounts"])


@router.get("")
async def list_bank_accounts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    type: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.view")),
) -> dict[str, Any]:
    handler = ListBankAccountsHandler(get_session_factory())
    result = await handler.handle(ListBankAccountsQuery(actor=actor, page=page, limit=limit, status=status, tipo=type))
    return {
        "data": [BankAccountResponse.from_dto(a) for a in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{bank_account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    bank_account_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.view")),
) -> BankAccountResponse:
    handler = GetBankAccountHandler(get_session_factory())
    dto = await handler.handle(GetBankAccountQuery(actor=actor, bank_account_id=bank_account_id))
    return BankAccountResponse.from_dto(dto)


@router.get("/{bank_account_id}/saldo", response_model=BankAccountBalanceResponse)
async def get_bank_account_balance(
    bank_account_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.view")),
) -> BankAccountBalanceResponse:
    handler = GetBankAccountBalanceHandler(get_session_factory())
    result = await handler.handle(GetBankAccountBalanceQuery(actor=actor, bank_account_id=bank_account_id))
    return BankAccountBalanceResponse.from_result(result)


@router.post("", response_model=BankAccountResponse, status_code=201)
async def create_bank_account(
    body: CreateBankAccountRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.create")),
) -> BankAccountResponse:
    handler = CreateBankAccountHandler()
    dto = await handler.handle(
        CreateBankAccountCommand(
            actor=actor, bank=body.bank, branch=body.branch, account_number=body.account_number,
            tipo=BankAccountType(body.type),
        )
    )
    return BankAccountResponse.from_dto(dto)


@router.patch("/{bank_account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    bank_account_id: uuid.UUID,
    body: UpdateBankAccountRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.edit")),
) -> BankAccountResponse:
    handler = UpdateBankAccountHandler()
    dto = await handler.handle(
        UpdateBankAccountCommand(
            actor=actor, bank_account_id=bank_account_id, bank=body.bank, branch=body.branch,
            status=BankAccountStatus(body.status) if body.status else None,
        )
    )
    return BankAccountResponse.from_dto(dto)


@router.delete("/{bank_account_id}", status_code=204, response_model=None)
async def delete_bank_account(
    bank_account_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.bank_account.delete")),
) -> None:
    handler = DeleteBankAccountHandler()
    await handler.handle(DeleteBankAccountCommand(actor=actor, bank_account_id=bank_account_id))
