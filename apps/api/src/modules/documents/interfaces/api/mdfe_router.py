from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from core.exceptions.base import NotFoundError
from modules.documents.application.commands.cancel_mdfe import CancelMdfeCommand, CancelMdfeHandler
from modules.documents.application.commands.close_mdfe import CloseMdfeCommand, CloseMdfeHandler
from modules.documents.application.commands.create_mdfe import CreateMdfeCommand, CreateMdfeHandler
from modules.documents.application.queries.get_mdfe import GetMdfeHandler, GetMdfeQuery
from modules.documents.application.queries.list_mdfe_status_history import (
    ListMdfeStatusHistoryHandler,
    ListMdfeStatusHistoryQuery,
)
from modules.documents.application.queries.list_mdfes import ListMdfesHandler, ListMdfesQuery
from modules.documents.interfaces.schemas.mdfe_schemas import CancelMdfeRequest, CreateMdfeRequest, MdfeResponse
from modules.documents.interfaces.schemas.status_history_schemas import StatusHistoryEntryResponse
from modules.documents.interfaces.schemas.xml_reference_schemas import XmlReferenceResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mdfes", tags=["MDF-e"])


@router.get("")
async def list_mdfes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    trip_id: uuid.UUID | None = None,
    status: str | None = None,
    series: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.view")),
) -> dict[str, Any]:
    handler = ListMdfesHandler(get_session_factory())
    result = await handler.handle(
        ListMdfesQuery(actor=actor, page=page, limit=limit, trip_id=trip_id, status=status, series=series)
    )
    return {
        "data": [MdfeResponse.from_dto(m) for m in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{mdfe_id}", response_model=MdfeResponse)
async def get_mdfe(
    mdfe_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.view"))
) -> MdfeResponse:
    handler = GetMdfeHandler(get_session_factory())
    dto = await handler.handle(GetMdfeQuery(actor=actor, mdfe_id=mdfe_id))
    return MdfeResponse.from_dto(dto)


@router.post("", response_model=MdfeResponse, status_code=201)
async def create_mdfe(
    body: CreateMdfeRequest, actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.issue"))
) -> MdfeResponse:
    handler = CreateMdfeHandler()
    dto = await handler.handle(CreateMdfeCommand(actor=actor, trip_id=body.trip_id, cte_ids=body.cte_ids))
    return MdfeResponse.from_dto(dto)


@router.post("/{mdfe_id}/commands/close", response_model=MdfeResponse)
async def close_mdfe(
    mdfe_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.close"))
) -> MdfeResponse:
    handler = CloseMdfeHandler()
    dto = await handler.handle(CloseMdfeCommand(actor=actor, mdfe_id=mdfe_id))
    return MdfeResponse.from_dto(dto)


@router.post("/{mdfe_id}/commands/cancel", response_model=MdfeResponse)
async def cancel_mdfe(
    mdfe_id: uuid.UUID, body: CancelMdfeRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.cancel")),
) -> MdfeResponse:
    handler = CancelMdfeHandler()
    dto = await handler.handle(CancelMdfeCommand(actor=actor, mdfe_id=mdfe_id, notes=body.notes))
    return MdfeResponse.from_dto(dto)


@router.get("/{mdfe_id}/status-history")
async def list_mdfe_status_history(
    mdfe_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.view")),
) -> dict[str, Any]:
    handler = ListMdfeStatusHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListMdfeStatusHistoryQuery(actor=actor, mdfe_id=mdfe_id, cursor=cursor, limit=limit, status=status)
    )
    return {
        "data": [StatusHistoryEntryResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.get("/{mdfe_id}/xml", response_model=XmlReferenceResponse)
async def get_mdfe_xml(
    mdfe_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.mdfe.view"))
) -> XmlReferenceResponse:
    handler = GetMdfeHandler(get_session_factory())
    dto = await handler.handle(GetMdfeQuery(actor=actor, mdfe_id=mdfe_id))
    if dto.xml_arquivo_id is None:
        raise NotFoundError("FISCAL_MDFE_XML_NOT_AVAILABLE", "MDF-e ainda não tem XML (antes de AUTORIZADO).")
    # `mdfes` só tem `data_hora_encerramento` como coluna de timestamp — antes de `ENCERRADO`, não
    # há dado real para popular `generated_at` (campo opcional no contrato, D276).
    return XmlReferenceResponse(xml_file_id=dto.xml_arquivo_id, generated_at=dto.data_hora_encerramento)
