from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.reporting.application.commands.create_saved_report import (
    CreateSavedReportCommand,
    CreateSavedReportHandler,
)
from modules.reporting.application.commands.delete_saved_report import (
    DeleteSavedReportCommand,
    DeleteSavedReportHandler,
)
from modules.reporting.application.commands.update_saved_report import (
    UpdateSavedReportCommand,
    UpdateSavedReportHandler,
)
from modules.reporting.application.queries.get_saved_report import GetSavedReportHandler, GetSavedReportQuery
from modules.reporting.application.queries.list_saved_reports import ListSavedReportsHandler, ListSavedReportsQuery
from modules.reporting.domain.value_objects.output_format import OutputFormat
from modules.reporting.interfaces.schemas.saved_report_schemas import (
    CreateSavedReportRequest,
    SavedReportResponse,
    UpdateSavedReportRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/reporting/saved-reports", tags=["Saved Reports"])


@router.get("")
async def list_saved_reports(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    output_format: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_report.view_own")),
) -> dict[str, Any]:
    handler = ListSavedReportsHandler(get_session_factory())
    result = await handler.handle(
        ListSavedReportsQuery(
            actor=actor, page=page, limit=limit, search=search, output_format=output_format, status=status
        )
    )
    return {
        "data": [SavedReportResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{saved_report_id}", response_model=SavedReportResponse)
async def get_saved_report(
    saved_report_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_report.view_own")),
) -> SavedReportResponse:
    handler = GetSavedReportHandler(get_session_factory())
    dto = await handler.handle(GetSavedReportQuery(actor=actor, saved_report_id=saved_report_id))
    return SavedReportResponse.from_dto(dto)


@router.post("", response_model=SavedReportResponse, status_code=201)
async def create_saved_report(
    body: CreateSavedReportRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_report.create")),
) -> SavedReportResponse:
    handler = CreateSavedReportHandler()
    dto = await handler.handle(
        CreateSavedReportCommand(
            actor=actor, name=body.name, metric_ids=body.metric_ids, filters=body.filters,
            output_format=OutputFormat(body.output_format),
        )
    )
    return SavedReportResponse.from_dto(dto)


@router.patch("/{saved_report_id}", response_model=SavedReportResponse)
async def update_saved_report(
    saved_report_id: uuid.UUID, body: UpdateSavedReportRequest,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_report.edit_own")),
) -> SavedReportResponse:
    handler = UpdateSavedReportHandler()
    dto = await handler.handle(
        UpdateSavedReportCommand(
            actor=actor, saved_report_id=saved_report_id, name=body.name, metric_ids=body.metric_ids,
            filters=body.filters,
            output_format=OutputFormat(body.output_format) if body.output_format is not None else None,
            status=body.status,
        )
    )
    return SavedReportResponse.from_dto(dto)


@router.delete("/{saved_report_id}", status_code=204, response_model=None)
async def delete_saved_report(
    saved_report_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("reporting.saved_report.delete_own")),
) -> None:
    handler = DeleteSavedReportHandler()
    await handler.handle(DeleteSavedReportCommand(actor=actor, saved_report_id=saved_report_id))
