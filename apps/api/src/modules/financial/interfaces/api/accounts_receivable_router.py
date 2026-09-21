from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.queries.list_accounts_receivable_global import (
    ListAccountsReceivableGlobalHandler,
    ListAccountsReceivableGlobalQuery,
)
from modules.financial.interfaces.schemas.accounts_receivable_schemas import AccountsReceivableResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

# Consulta agregada entre Faturas (Lote Financeiro, Parte 2.1) — "o que tenho para receber hoje"
# sem abrir Fatura por Fatura. Prefixo próprio, não aninhado sob `/faturas` (`invoice_router.py`),
# porque esta consulta atravessa Faturas — ownership do domínio não muda (Conta a Receber continua
# sub-recurso de Fatura, D260), só a superfície de leitura ganha uma rota própria.
router = APIRouter(prefix="/contas-receber", tags=["Accounts Receivable"])


@router.get("")
async def list_accounts_receivable(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    client_id: uuid.UUID | None = None,
    accounting_period: date | None = None,
    due_date__gte: date | None = None,
    due_date__lte: date | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.receivable.view")),
) -> dict[str, Any]:
    handler = ListAccountsReceivableGlobalHandler(get_session_factory())
    result = await handler.handle(
        ListAccountsReceivableGlobalQuery(
            actor=actor, page=page, limit=limit, status=status, client_id=client_id,
            accounting_period=accounting_period, due_date_from=due_date__gte, due_date_to=due_date__lte,
        )
    )
    return {
        "data": [AccountsReceivableResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }
