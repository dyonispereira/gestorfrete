from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.financial.application.commands.create_payment_method import (
    CreatePaymentMethodCommand,
    CreatePaymentMethodHandler,
)
from modules.financial.application.commands.update_payment_method import (
    UpdatePaymentMethodCommand,
    UpdatePaymentMethodHandler,
)
from modules.financial.application.queries.get_payment_method import GetPaymentMethodHandler, GetPaymentMethodQuery
from modules.financial.application.queries.list_payment_methods import (
    ListPaymentMethodsHandler,
    ListPaymentMethodsQuery,
)
from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from modules.financial.interfaces.schemas.payment_method_schemas import (
    CreatePaymentMethodRequest,
    PaymentMethodResponse,
    UpdatePaymentMethodRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

# D386, fechado (Lote Financeiro, Parte 2.1) — Entidade/Repository já existiam desde a Parte 2;
# faltava exposição HTTP, o que forçava a UI a usar um campo de ID cru para forma de pagamento.
router = APIRouter(prefix="/formas-pagamento", tags=["Payment Methods"])


@router.get("")
async def list_payment_methods(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("financial.payment_method.view")),
) -> dict[str, Any]:
    handler = ListPaymentMethodsHandler(get_session_factory())
    result = await handler.handle(ListPaymentMethodsQuery(actor=actor, page=page, limit=limit, status=status))
    return {
        "data": [PaymentMethodResponse.from_dto(p) for p in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("financial.payment_method.view")),
) -> PaymentMethodResponse:
    handler = GetPaymentMethodHandler(get_session_factory())
    dto = await handler.handle(GetPaymentMethodQuery(actor=actor, payment_method_id=payment_method_id))
    return PaymentMethodResponse.from_dto(dto)


@router.post("", response_model=PaymentMethodResponse, status_code=201)
async def create_payment_method(
    body: CreatePaymentMethodRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payment_method.create")),
) -> PaymentMethodResponse:
    handler = CreatePaymentMethodHandler()
    dto = await handler.handle(CreatePaymentMethodCommand(actor=actor, nome=body.nome))
    return PaymentMethodResponse.from_dto(dto)


@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: uuid.UUID,
    body: UpdatePaymentMethodRequest,
    actor: AuthenticatedActor = Depends(require_permission("financial.payment_method.edit")),
) -> PaymentMethodResponse:
    handler = UpdatePaymentMethodHandler()
    dto = await handler.handle(
        UpdatePaymentMethodCommand(
            actor=actor, payment_method_id=payment_method_id, nome=body.nome,
            status=PaymentMethodStatus(body.status) if body.status else None,
        )
    )
    return PaymentMethodResponse.from_dto(dto)


# Sem DELETE — mesmo padrão de CostCenter/ChartOfAccounts (D216-style): status INATIVA via PATCH
# é a forma real de "desativar", nunca exclusão física de um cadastro mestre referenciado por FK.
