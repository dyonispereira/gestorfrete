from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.commands.process_sync_batch import (
    ProcessSyncBatchCommand,
    ProcessSyncBatchHandler,
    SyncCommandInput,
)
from modules.mobile.application.queries.list_sync_records import ListSyncRecordsHandler, ListSyncRecordsQuery
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.interfaces.dependencies import get_current_mobile_session
from modules.mobile.interfaces.schemas.sync_schemas import SyncBatchRequest, SyncBatchResponse, SyncRecordResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile", tags=["Mobile Sync"])


@router.post("/sync", response_model=SyncBatchResponse)
async def sync(
    body: SyncBatchRequest, actor: AuthenticatedActor = Depends(require_permission("mobile.sync.execute")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> SyncBatchResponse:
    handler = ProcessSyncBatchHandler()
    result = await handler.handle(
        ProcessSyncBatchCommand(
            actor=actor, session_id=mobile_session.id,
            commands=[
                SyncCommandInput(
                    local_id=c.local_id, sequence=c.sequence, command=c.command,
                    target_entity_type=c.target_entity_type, target_entity_id=c.target_entity_id, payload=c.payload,
                )
                for c in body.commands
            ],
        )
    )
    return SyncBatchResponse.from_dto(result)


@router.get("/sync/records")
async def list_sync_records(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("mobile.sync.execute")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> dict[str, Any]:
    handler = ListSyncRecordsHandler(get_session_factory())
    result = await handler.handle(
        ListSyncRecordsQuery(actor=actor, session_id=mobile_session.id, page=page, limit=limit)
    )
    return {
        "data": [SyncRecordResponse.from_dto(r) for r in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }
