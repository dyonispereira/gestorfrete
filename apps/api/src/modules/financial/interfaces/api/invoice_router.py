from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.cancel_invoice import CancelInvoiceCommand, CancelInvoiceHandler
from modules.financial.application.commands.confirm_receipt_accounts_receivable import (
    ConfirmReceiptAccountsReceivableCommand,
    ConfirmReceiptAccountsReceivableHandler,
)
from modules.financial.application.commands.create_accounts_receivable import (
    CreateAccountsReceivableCommand,
    CreateAccountsReceivableHandler,
)
from modules.financial.application.commands.create_invoice import (
    CreateInvoiceCommand,
    CreateInvoiceHandler,
    InvoiceInstallmentInput,
)
from modules.financial.application.commands.update_accounts_receivable import (
    UpdateAccountsReceivableCommand,
    UpdateAccountsReceivableHandler,
)
from modules.financial.application.queries.get_accounts_receivable import (
    GetAccountsReceivableHandler,
    GetAccountsReceivableQuery,
)
from modules.financial.application.queries.get_invoice import GetInvoiceHandler, GetInvoiceQuery
from modules.financial.application.queries.list_accounts_receivable import (
    ListAccountsReceivableHandler,
    ListAccountsReceivableQuery,
)
from modules.financial.application.queries.list_invoices import ListInvoicesHandler, ListInvoicesQuery
from modules.financial.interfaces.schemas.accounts_receivable_schemas import (
    AccountsReceivableResponse,
    ConfirmReceiptRequest,
    CreateAccountsReceivableRequest,
    UpdateAccountsReceivableRequest,
)
from modules.financial.interfaces.schemas.invoice_schemas import (
    CreateInvoiceRequest,
    InvoiceResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/faturas", tags=["Invoices"])


@router.get("")
async def list_invoices(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    client_id: uuid.UUID | None = None,
    status: str | None = None,
    trip_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.invoice.view")),
) -> dict[str, Any]:
    handler = ListInvoicesHandler(get_session_factory())
    result = await handler.handle(
        ListInvoicesQuery(actor=actor, page=page, limit=limit, client_id=client_id, status=status, trip_id=trip_id)
    )
    return {
        "data": [InvoiceResponse.from_dto(i) for i in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.invoice.view")),
) -> InvoiceResponse:
    handler = GetInvoiceHandler(get_session_factory())
    dto = await handler.handle(GetInvoiceQuery(actor=actor, invoice_id=invoice_id))
    return InvoiceResponse.from_dto(dto)


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    body: CreateInvoiceRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.invoice.create")),
) -> InvoiceResponse:
    handler = CreateInvoiceHandler()
    dto = await handler.handle(
        CreateInvoiceCommand(
            actor=actor, trip_id=body.trip_id, delivery_id=body.delivery_id, client_id=body.client_id,
            total_value=body.total_value, payment_method_id=body.payment_method_id,
            installments=[InvoiceInstallmentInput(value=i.value, due_date=i.due_date) for i in body.installments],
        )
    )
    return InvoiceResponse.from_dto(dto)


@router.post("/{invoice_id}/commands/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.invoice.cancel")),
) -> InvoiceResponse:
    handler = CancelInvoiceHandler()
    dto = await handler.handle(CancelInvoiceCommand(actor=actor, invoice_id=invoice_id))
    return InvoiceResponse.from_dto(dto)


@router.get("/{invoice_id}/contas-receber")
async def list_accounts_receivable(
    invoice_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.view")),
) -> dict[str, Any]:
    handler = ListAccountsReceivableHandler(get_session_factory())
    receivables = await handler.handle(ListAccountsReceivableQuery(actor=actor, invoice_id=invoice_id))
    items = [AccountsReceivableResponse.from_dto(r) for r in receivables]
    return {"data": items, "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}}}


@router.get("/{invoice_id}/contas-receber/{parcela_id}", response_model=AccountsReceivableResponse)
async def get_accounts_receivable(
    invoice_id: uuid.UUID,
    parcela_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.view")),
) -> AccountsReceivableResponse:
    handler = GetAccountsReceivableHandler(get_session_factory())
    dto = await handler.handle(GetAccountsReceivableQuery(actor=actor, accounts_receivable_id=parcela_id))
    return AccountsReceivableResponse.from_dto(dto)


@router.post("/{invoice_id}/contas-receber", response_model=AccountsReceivableResponse, status_code=201)
async def create_accounts_receivable(
    invoice_id: uuid.UUID,
    body: CreateAccountsReceivableRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.create")),
) -> AccountsReceivableResponse:
    handler = CreateAccountsReceivableHandler()
    dto = await handler.handle(
        CreateAccountsReceivableCommand(
            actor=actor, invoice_id=invoice_id, valor=body.value, data_vencimento=body.due_date
        )
    )
    return AccountsReceivableResponse.from_dto(dto)


@router.patch("/{invoice_id}/contas-receber/{parcela_id}", response_model=AccountsReceivableResponse)
async def update_accounts_receivable(
    invoice_id: uuid.UUID,
    parcela_id: uuid.UUID,
    body: UpdateAccountsReceivableRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.edit")),
) -> AccountsReceivableResponse:
    handler = UpdateAccountsReceivableHandler()
    dto = await handler.handle(
        UpdateAccountsReceivableCommand(
            actor=actor, invoice_id=invoice_id, accounts_receivable_id=parcela_id, valor=body.value,
            data_vencimento=body.due_date,
        )
    )
    return AccountsReceivableResponse.from_dto(dto)


@router.post(
    "/{invoice_id}/contas-receber/{parcela_id}/commands/confirm-receipt", response_model=AccountsReceivableResponse
)
async def confirm_receipt_accounts_receivable(
    invoice_id: uuid.UUID,
    parcela_id: uuid.UUID,
    body: ConfirmReceiptRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.confirm_receipt")),
) -> AccountsReceivableResponse:
    handler = ConfirmReceiptAccountsReceivableHandler()
    dto = await handler.handle(
        ConfirmReceiptAccountsReceivableCommand(
            actor=actor, invoice_id=invoice_id, accounts_receivable_id=parcela_id, received_value=body.received_value
        )
    )
    return AccountsReceivableResponse.from_dto(dto)
