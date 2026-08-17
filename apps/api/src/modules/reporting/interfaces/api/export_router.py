from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.reporting.application.commands.create_export import CreateExportCommand, CreateExportHandler
from modules.reporting.application.queries.get_export import GetExportHandler, GetExportQuery
from modules.reporting.application.queries.list_exports import ListExportsHandler, ListExportsQuery
from modules.reporting.interfaces.schemas.export_schemas import CreateExportRequest, ExportResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/reporting/exports", tags=["Exports"])


@router.get("")
async def list_exports(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    saved_report_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("reporting.export.view_own")),
) -> dict[str, Any]:
    handler = ListExportsHandler(get_session_factory())
    result = await handler.handle(
        ListExportsQuery(actor=actor, page=page, limit=limit, status=status, saved_report_id=saved_report_id)
    )
    return {
        "data": [ExportResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("reporting.export.view_own"))
) -> ExportResponse:
    handler = GetExportHandler(get_session_factory())
    dto = await handler.handle(GetExportQuery(actor=actor, export_id=export_id))
    return ExportResponse.from_dto(dto)


@router.post("", response_model=ExportResponse, status_code=201)
async def create_export(
    body: CreateExportRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: AuthenticatedActor = Depends(require_permission("reporting.export.create")),
) -> ExportResponse:
    # D418 — `Idempotency-Key` aceito/documentado, sem enforcement real (gap pré-existente do
    # projeto inteiro desde o Lote 2, ver DECISIONS.md).
    handler = CreateExportHandler()
    dto = await handler.handle(
        CreateExportCommand(
            actor=actor, saved_report_id=body.saved_report_id, filters=body.filters, period=body.period
        )
    )
    return ExportResponse.from_dto(dto)
