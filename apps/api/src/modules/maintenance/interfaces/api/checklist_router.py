from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.maintenance.application.commands.approve_checklist import ApproveChecklistCommand, ApproveChecklistHandler
from modules.maintenance.application.commands.create_checklist import CreateChecklistCommand, CreateChecklistHandler
from modules.maintenance.application.commands.reject_checklist import RejectChecklistCommand, RejectChecklistHandler
from modules.maintenance.application.commands.start_checklist import StartChecklistCommand, StartChecklistHandler
from modules.maintenance.application.commands.submit_checklist import SubmitChecklistCommand, SubmitChecklistHandler
from modules.maintenance.application.queries.get_checklist import GetChecklistHandler, GetChecklistQuery
from modules.maintenance.application.queries.list_checklist_status_history import (
    ListChecklistStatusHistoryHandler,
    ListChecklistStatusHistoryQuery,
)
from modules.maintenance.application.queries.list_checklists import ListChecklistsHandler, ListChecklistsQuery
from modules.maintenance.interfaces.schemas.checklist_schemas import (
    ChecklistResponse,
    ChecklistStatusHistoryEntryResponse,
    CreateChecklistRequest,
    RejectChecklistRequest,
    SubmitChecklistRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/checklists", tags=["Checklists"])


@router.get("")
async def list_checklists(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.view")),
) -> dict[str, Any]:
    handler = ListChecklistsHandler(get_session_factory())
    result = await handler.handle(
        ListChecklistsQuery(
            actor=actor, page=page, limit=limit, referencia_tipo=reference_type, referencia_id=reference_id,
            tipo=type, status=status,
        )
    )
    return {
        "data": [ChecklistResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    checklist_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.view"))
) -> ChecklistResponse:
    handler = GetChecklistHandler(get_session_factory())
    dto = await handler.handle(GetChecklistQuery(actor=actor, checklist_id=checklist_id))
    return ChecklistResponse.from_dto(dto)


@router.post("", response_model=ChecklistResponse, status_code=201)
async def create_checklist(
    body: CreateChecklistRequest, actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.fill"))
) -> ChecklistResponse:
    handler = CreateChecklistHandler()
    dto = await handler.handle(
        CreateChecklistCommand(
            actor=actor, tipo=body.type, referencia_tipo=body.reference_type, referencia_id=body.reference_id
        )
    )
    return ChecklistResponse.from_dto(dto)


@router.post("/{checklist_id}/commands/start", response_model=ChecklistResponse)
async def start_checklist(
    checklist_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.fill"))
) -> ChecklistResponse:
    handler = StartChecklistHandler()
    dto = await handler.handle(StartChecklistCommand(actor=actor, checklist_id=checklist_id))
    return ChecklistResponse.from_dto(dto)


@router.post("/{checklist_id}/commands/submit", response_model=ChecklistResponse)
async def submit_checklist(
    checklist_id: uuid.UUID, body: SubmitChecklistRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.fill")),
) -> ChecklistResponse:
    handler = SubmitChecklistHandler()
    dto = await handler.handle(
        SubmitChecklistCommand(
            actor=actor, checklist_id=checklist_id, itens=[item.model_dump() for item in body.itens]
        )
    )
    return ChecklistResponse.from_dto(dto)


@router.post("/{checklist_id}/commands/approve", response_model=ChecklistResponse)
async def approve_checklist(
    checklist_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.approve"))
) -> ChecklistResponse:
    handler = ApproveChecklistHandler()
    dto = await handler.handle(ApproveChecklistCommand(actor=actor, checklist_id=checklist_id))
    return ChecklistResponse.from_dto(dto)


@router.post("/{checklist_id}/commands/reject", response_model=ChecklistResponse)
async def reject_checklist(
    checklist_id: uuid.UUID, body: RejectChecklistRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.reject")),
) -> ChecklistResponse:
    handler = RejectChecklistHandler()
    dto = await handler.handle(
        RejectChecklistCommand(actor=actor, checklist_id=checklist_id, observacao=body.observacao)
    )
    return ChecklistResponse.from_dto(dto)


@router.get("/{checklist_id}/status-history")
async def list_checklist_status_history(
    checklist_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.checklist.view_history")),
) -> dict[str, Any]:
    handler = ListChecklistStatusHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListChecklistStatusHistoryQuery(actor=actor, checklist_id=checklist_id, cursor=cursor, limit=limit, status=status)
    )
    return {
        "data": [
            ChecklistStatusHistoryEntryResponse(
                id=e.id, status=e.status, user_id=e.usuario_id, origin=e.origem, notes=e.observacao,
                occurred_at=e.data_hora,
            )
            for e in result.items
        ],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }
