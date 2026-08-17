from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.create_financial_reversal import (
    CreateFinancialReversalCommand,
    CreateFinancialReversalHandler,
)
from modules.financial.application.queries.get_financial_reversal import (
    GetFinancialReversalHandler,
    GetFinancialReversalQuery,
)
from modules.financial.application.queries.list_financial_reversals import (
    ListFinancialReversalsHandler,
    ListFinancialReversalsQuery,
)
from modules.financial.interfaces.schemas.financial_reversal_schemas import (
    CreateFinancialReversalRequest,
    FinancialReversalResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/estornos-financeiros", tags=["Financial Reversals"])


@router.get("")
async def list_financial_reversals(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    invoice_id: uuid.UUID | None = None,
    accounts_payable_id: uuid.UUID | None = None,
    accounts_receivable_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.reversal.view")),
) -> dict[str, Any]:
    handler = ListFinancialReversalsHandler(get_session_factory())
    result = await handler.handle(
        ListFinancialReversalsQuery(
            actor=actor, page=page, limit=limit, invoice_id=invoice_id,
            accounts_payable_id=accounts_payable_id, accounts_receivable_id=accounts_receivable_id,
        )
    )
    return {
        "data": [FinancialReversalResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{financial_reversal_id}", response_model=FinancialReversalResponse)
async def get_financial_reversal(
    financial_reversal_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.reversal.view")),
) -> FinancialReversalResponse:
    handler = GetFinancialReversalHandler(get_session_factory())
    dto = await handler.handle(GetFinancialReversalQuery(actor=actor, financial_reversal_id=financial_reversal_id))
    return FinancialReversalResponse.from_dto(dto)


@router.post("", response_model=FinancialReversalResponse, status_code=201)
async def create_financial_reversal(
    body: CreateFinancialReversalRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.reversal.create")),
) -> FinancialReversalResponse:
    handler = CreateFinancialReversalHandler()
    dto = await handler.handle(
        CreateFinancialReversalCommand(
            actor=actor, invoice_id=body.invoice_id, accounts_payable_id=body.accounts_payable_id,
            accounts_receivable_id=body.accounts_receivable_id, valor=body.value, motivo=body.reason,
        )
    )
    return FinancialReversalResponse.from_dto(dto)
