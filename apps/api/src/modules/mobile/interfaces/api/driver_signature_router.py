from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.queries.get_signature import GetSignatureHandler, GetSignatureQuery
from modules.mobile.application.queries.list_signatures import ListSignaturesHandler, ListSignaturesQuery
from modules.mobile.interfaces.schemas.signature_schemas import DigitalSignatureResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/signatures", tags=["Mobile Signatures"])


@router.get("")
async def list_signatures(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    document_type: str | None = None,
    document_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view")),
) -> dict[str, Any]:
    handler = ListSignaturesHandler(get_session_factory())
    result = await handler.handle(
        ListSignaturesQuery(actor=actor, page=page, limit=limit, document_type=document_type, document_id=document_id)
    )
    return {
        "data": [DigitalSignatureResponse.from_dto(s) for s in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{signature_id}", response_model=DigitalSignatureResponse)
async def get_signature(
    signature_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view"))
) -> DigitalSignatureResponse:
    handler = GetSignatureHandler(get_session_factory())
    dto = await handler.handle(GetSignatureQuery(actor=actor, signature_id=signature_id))
    return DigitalSignatureResponse.from_dto(dto)
