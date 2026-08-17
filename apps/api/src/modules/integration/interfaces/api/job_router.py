from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.integration.application.commands.trigger_job import TriggerJobCommand, TriggerJobHandler
from modules.integration.application.queries.get_job import GetJobHandler, GetJobQuery
from modules.integration.application.queries.list_jobs import ListJobsHandler, ListJobsQuery
from modules.integration.interfaces.schemas.job_schemas import JobExecutionResponse, TriggerJobRequest
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
async def list_jobs(
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    job_type: str | None = None,
    result: str | None = None,
    started_at__gte: datetime | None = None,
    started_at__lte: datetime | None = None,
    actor: AuthenticatedActor = Depends(require_permission("integration.job.view")),
) -> dict[str, Any]:
    handler = ListJobsHandler(get_session_factory())
    page = await handler.handle(
        ListJobsQuery(
            actor=actor, cursor=cursor, limit=limit, job_type=job_type, result=result,
            started_at_gte=started_at__gte, started_at_lte=started_at__lte,
        )
    )
    return {
        "data": [JobExecutionResponse.from_dto(e) for e in page.items],
        "meta": {"pagination": {"next_cursor": page.next_cursor, "has_more": page.has_more}},
    }


@router.get("/{job_id}", response_model=JobExecutionResponse)
async def get_job(
    job_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.job.view"))
) -> JobExecutionResponse:
    handler = GetJobHandler(get_session_factory())
    dto = await handler.handle(GetJobQuery(actor=actor, job_id=job_id))
    return JobExecutionResponse.from_dto(dto)


@router.post("/commands/trigger", response_model=JobExecutionResponse, status_code=202)
async def trigger_job(
    body: TriggerJobRequest, actor: AuthenticatedActor = Depends(require_permission("integration.job.trigger"))
) -> JobExecutionResponse:
    handler = TriggerJobHandler()
    dto = await handler.handle(TriggerJobCommand(actor=actor, job_type=body.job_type, parameters=body.parameters))
    return JobExecutionResponse.from_dto(dto)
