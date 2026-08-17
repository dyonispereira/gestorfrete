from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.documents.application.commands.cancel_ciot import CancelCiotCommand, CancelCiotHandler
from modules.documents.application.commands.create_ciot import CreateCiotCommand, CreateCiotHandler
from modules.documents.application.commands.register_ciot import RegisterCiotCommand, RegisterCiotHandler
from modules.documents.application.queries.get_ciot import GetCiotHandler, GetCiotQuery
from modules.documents.application.queries.list_ciot_status_history import (
    ListCiotStatusHistoryHandler,
    ListCiotStatusHistoryQuery,
)
from modules.documents.application.queries.list_ciots import ListCiotsHandler, ListCiotsQuery
from modules.documents.interfaces.schemas.ciot_schemas import CancelCiotRequest, CiotResponse, CreateCiotRequest
from modules.documents.interfaces.schemas.status_history_schemas import StatusHistoryEntryResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ciots", tags=["CIOT"])


@router.get("")
async def list_ciots(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    trip_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.ciot.view")),
) -> dict[str, Any]:
    handler = ListCiotsHandler(get_session_factory())
    result = await handler.handle(
        ListCiotsQuery(actor=actor, page=page, limit=limit, trip_id=trip_id, driver_id=driver_id, status=status)
    )
    return {
        "data": [CiotResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{ciot_id}", response_model=CiotResponse)
async def get_ciot(
    ciot_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.ciot.view"))
) -> CiotResponse:
    handler = GetCiotHandler(get_session_factory())
    dto = await handler.handle(GetCiotQuery(actor=actor, ciot_id=ciot_id))
    return CiotResponse.from_dto(dto)


@router.post("", response_model=CiotResponse, status_code=201)
async def create_ciot(
    body: CreateCiotRequest, actor: AuthenticatedActor = Depends(require_permission("documents.ciot.register"))
) -> CiotResponse:
    handler = CreateCiotHandler()
    dto = await handler.handle(CreateCiotCommand(actor=actor, trip_id=body.trip_id, driver_id=body.driver_id))
    return CiotResponse.from_dto(dto)


@router.post("/{ciot_id}/commands/register", response_model=CiotResponse)
async def register_ciot(
    ciot_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.ciot.register"))
) -> CiotResponse:
    handler = RegisterCiotHandler()
    dto = await handler.handle(RegisterCiotCommand(actor=actor, ciot_id=ciot_id))
    return CiotResponse.from_dto(dto)


@router.post("/{ciot_id}/commands/cancel", response_model=CiotResponse)
async def cancel_ciot(
    ciot_id: uuid.UUID, body: CancelCiotRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.ciot.cancel")),
) -> CiotResponse:
    handler = CancelCiotHandler()
    dto = await handler.handle(CancelCiotCommand(actor=actor, ciot_id=ciot_id, notes=body.notes))
    return CiotResponse.from_dto(dto)


@router.get("/{ciot_id}/status-history")
async def list_ciot_status_history(
    ciot_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.ciot.view")),
) -> dict[str, Any]:
    handler = ListCiotStatusHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListCiotStatusHistoryQuery(actor=actor, ciot_id=ciot_id, cursor=cursor, limit=limit, status=status)
    )
    return {
        "data": [StatusHistoryEntryResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
