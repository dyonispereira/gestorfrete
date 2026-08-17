from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.documents.application.queries.get_fiscal_event import GetFiscalEventHandler, GetFiscalEventQuery
from modules.documents.application.queries.list_fiscal_events import (
    ListFiscalEventsHandler,
    ListFiscalEventsQuery,
)
from modules.documents.interfaces.schemas.fiscal_event_schemas import FiscalEventResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/fiscal/events", tags=["Fiscal Events"])


@router.get("")
async def list_fiscal_events(
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    document_type: str | None = None,
    document_id: uuid.UUID | None = None,
    external_protocol: str | None = None,
    started_at__gte: datetime | None = None,
    started_at__lte: datetime | None = None,
    result: str | None = None,
    origin: str | None = None,
    attempt_number: int | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.sefaz_status.view")),
) -> dict[str, Any]:
    handler = ListFiscalEventsHandler(get_session_factory())
    query_result = await handler.handle(
        ListFiscalEventsQuery(
            actor=actor, cursor=cursor, limit=limit, document_type=document_type, document_id=document_id,
            external_protocol=external_protocol, started_at_from=started_at__gte, started_at_to=started_at__lte,
            result=result, origin=origin, attempt_number=attempt_number,
        )
    )
    return {
        "data": [FiscalEventResponse.from_dto(e) for e in query_result.items],
        "meta": {"pagination": {"next_cursor": query_result.next_cursor, "has_more": query_result.has_more}},
    }


@router.get("/{fiscal_event_id}", response_model=FiscalEventResponse)
async def get_fiscal_event(
    fiscal_event_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("documents.sefaz_status.view")),
) -> FiscalEventResponse:
    handler = GetFiscalEventHandler(get_session_factory())
    dto = await handler.handle(GetFiscalEventQuery(actor=actor, fiscal_event_id=fiscal_event_id))
    return FiscalEventResponse.from_dto(dto)
