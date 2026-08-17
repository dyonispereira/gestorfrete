from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from core.exceptions.base import NotFoundError
from modules.documents.application.commands.cancel_cte import CancelCteCommand, CancelCteHandler
from modules.documents.application.commands.create_correction_letter import (
    CreateCorrectionLetterCommand,
    CreateCorrectionLetterHandler,
)
from modules.documents.application.commands.create_referenced_nfe import (
    CreateReferencedNfeCommand,
    CreateReferencedNfeHandler,
)
from modules.documents.application.commands.inutilize_cte import InutilizeCteCommand, InutilizeCteHandler
from modules.documents.application.commands.sign_cte import SignCteCommand, SignCteHandler
from modules.documents.application.commands.transmit_cte import TransmitCteCommand, TransmitCteHandler
from modules.documents.application.commands.validate_cte import ValidateCteCommand, ValidateCteHandler
from modules.documents.application.queries.get_correction_letter import (
    GetCorrectionLetterHandler,
    GetCorrectionLetterQuery,
)
from modules.documents.application.queries.get_cte import GetCteHandler, GetCteQuery
from modules.documents.application.queries.get_referenced_nfe import GetReferencedNfeHandler, GetReferencedNfeQuery
from modules.documents.application.queries.list_correction_letters import (
    ListCorrectionLettersHandler,
    ListCorrectionLettersQuery,
)
from modules.documents.application.queries.list_cte_status_history import (
    ListCteStatusHistoryHandler,
    ListCteStatusHistoryQuery,
)
from modules.documents.application.queries.list_ctes import ListCtesHandler, ListCtesQuery
from modules.documents.application.queries.list_referenced_nfes import (
    ListReferencedNfesHandler,
    ListReferencedNfesQuery,
)
from modules.documents.interfaces.schemas.correction_letter_schemas import (
    CorrectionLetterResponse,
    CreateCorrectionLetterRequest,
)
from modules.documents.interfaces.schemas.cte_schemas import CancelCteRequest, CteResponse
from modules.documents.interfaces.schemas.referenced_nfe_schemas import (
    CreateReferencedNfeRequest,
    ReferencedNfeResponse,
)
from modules.documents.interfaces.schemas.status_history_schemas import StatusHistoryEntryResponse
from modules.documents.interfaces.schemas.xml_reference_schemas import XmlReferenceResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ctes", tags=["CT-e"])


@router.get("")
async def list_ctes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    trip_id: uuid.UUID | None = None,
    status: str | None = None,
    series: str | None = None,
    access_key: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.view")),
) -> dict[str, Any]:
    handler = ListCtesHandler(get_session_factory())
    result = await handler.handle(
        ListCtesQuery(
            actor=actor, page=page, limit=limit, trip_id=trip_id, status=status, series=series,
            access_key=access_key,
        )
    )
    return {
        "data": [CteResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{cte_id}", response_model=CteResponse)
async def get_cte(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.view"))
) -> CteResponse:
    handler = GetCteHandler(get_session_factory())
    dto = await handler.handle(GetCteQuery(actor=actor, cte_id=cte_id))
    return CteResponse.from_dto(dto)


@router.post("/{cte_id}/commands/validate", response_model=CteResponse)
async def validate_cte(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.issue"))
) -> CteResponse:
    handler = ValidateCteHandler()
    dto = await handler.handle(ValidateCteCommand(actor=actor, cte_id=cte_id))
    return CteResponse.from_dto(dto)


@router.post("/{cte_id}/commands/sign", response_model=CteResponse)
async def sign_cte(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.issue"))
) -> CteResponse:
    handler = SignCteHandler()
    dto = await handler.handle(SignCteCommand(actor=actor, cte_id=cte_id))
    return CteResponse.from_dto(dto)


@router.post("/{cte_id}/commands/transmit", response_model=CteResponse)
async def transmit_cte(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.issue"))
) -> CteResponse:
    handler = TransmitCteHandler()
    dto = await handler.handle(TransmitCteCommand(actor=actor, cte_id=cte_id))
    return CteResponse.from_dto(dto)


@router.post("/{cte_id}/commands/cancel", response_model=CteResponse)
async def cancel_cte(
    cte_id: uuid.UUID, body: CancelCteRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.cancel")),
) -> CteResponse:
    handler = CancelCteHandler()
    dto = await handler.handle(CancelCteCommand(actor=actor, cte_id=cte_id, notes=body.notes))
    return CteResponse.from_dto(dto)


@router.post("/{cte_id}/commands/inutilize", response_model=CteResponse)
async def inutilize_cte(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.issue"))
) -> CteResponse:
    handler = InutilizeCteHandler()
    dto = await handler.handle(InutilizeCteCommand(actor=actor, cte_id=cte_id))
    return CteResponse.from_dto(dto)


@router.get("/{cte_id}/status-history")
async def list_cte_status_history(
    cte_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.view")),
) -> dict[str, Any]:
    handler = ListCteStatusHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListCteStatusHistoryQuery(actor=actor, cte_id=cte_id, cursor=cursor, limit=limit, status=status)
    )
    return {
        "data": [StatusHistoryEntryResponse.from_dto(e) for e in result.items],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.get("/{cte_id}/xml", response_model=XmlReferenceResponse)
async def get_cte_xml(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.view"))
) -> XmlReferenceResponse:
    handler = GetCteHandler(get_session_factory())
    dto = await handler.handle(GetCteQuery(actor=actor, cte_id=cte_id))
    if dto.xml_arquivo_id is None:
        raise NotFoundError("FISCAL_CTE_XML_NOT_AVAILABLE", "CT-e ainda não tem XML (antes de AUTORIZADO).")
    return XmlReferenceResponse(xml_file_id=dto.xml_arquivo_id, generated_at=dto.data_hora_autorizacao)


@router.get("/{cte_id}/cartas-correcao")
async def list_correction_letters(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.cte.correct"))
) -> dict[str, Any]:
    handler = ListCorrectionLettersHandler(get_session_factory())
    letters = await handler.handle(ListCorrectionLettersQuery(actor=actor, cte_id=cte_id))
    items = [CorrectionLetterResponse.from_dto(letter) for letter in letters]
    return {"data": items, "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}}}


@router.get("/{cte_id}/cartas-correcao/{carta_id}", response_model=CorrectionLetterResponse)
async def get_correction_letter(
    cte_id: uuid.UUID, carta_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.correct")),
) -> CorrectionLetterResponse:
    handler = GetCorrectionLetterHandler(get_session_factory())
    dto = await handler.handle(GetCorrectionLetterQuery(actor=actor, correction_letter_id=carta_id))
    if dto.cte_id != cte_id:
        raise NotFoundError("FISCAL_CORRECTION_LETTER_NOT_FOUND", "Carta de Correção não encontrada.")
    return CorrectionLetterResponse.from_dto(dto)


@router.post("/{cte_id}/cartas-correcao", response_model=CorrectionLetterResponse, status_code=201)
async def create_correction_letter(
    cte_id: uuid.UUID, body: CreateCorrectionLetterRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.correct")),
) -> CorrectionLetterResponse:
    handler = CreateCorrectionLetterHandler()
    dto = await handler.handle(
        CreateCorrectionLetterCommand(actor=actor, cte_id=cte_id, correction_text=body.correction_text)
    )
    return CorrectionLetterResponse.from_dto(dto)


@router.get("/{cte_id}/cartas-correcao/{carta_id}/xml", response_model=XmlReferenceResponse)
async def get_correction_letter_xml(
    cte_id: uuid.UUID, carta_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.correct")),
) -> XmlReferenceResponse:
    handler = GetCorrectionLetterHandler(get_session_factory())
    dto = await handler.handle(GetCorrectionLetterQuery(actor=actor, correction_letter_id=carta_id))
    if dto.cte_id != cte_id or dto.xml_arquivo_id is None:
        raise NotFoundError("FISCAL_CORRECTION_LETTER_XML_NOT_AVAILABLE", "XML da Carta de Correção não disponível.")
    return XmlReferenceResponse(xml_file_id=dto.xml_arquivo_id, generated_at=dto.data_hora_envio)


@router.get("/{cte_id}/nfe-referenciadas")
async def list_referenced_nfes(
    cte_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("documents.nfe_reference.view"))
) -> dict[str, Any]:
    handler = ListReferencedNfesHandler(get_session_factory())
    nfes = await handler.handle(ListReferencedNfesQuery(actor=actor, cte_id=cte_id))
    items = [ReferencedNfeResponse.from_dto(nfe) for nfe in nfes]
    return {"data": items, "meta": {"pagination": {"page": 1, "limit": len(items), "total": len(items)}}}


@router.get("/{cte_id}/nfe-referenciadas/{nfe_id}", response_model=ReferencedNfeResponse)
async def get_referenced_nfe(
    cte_id: uuid.UUID, nfe_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("documents.nfe_reference.view")),
) -> ReferencedNfeResponse:
    handler = GetReferencedNfeHandler(get_session_factory())
    dto = await handler.handle(GetReferencedNfeQuery(actor=actor, referenced_nfe_id=nfe_id))
    if dto.cte_id != cte_id:
        raise NotFoundError("FISCAL_NFE_REFERENCE_NOT_FOUND", "NF-e Referenciada não encontrada.")
    return ReferencedNfeResponse.from_dto(dto)


@router.post("/{cte_id}/nfe-referenciadas", response_model=ReferencedNfeResponse, status_code=201)
async def create_referenced_nfe(
    cte_id: uuid.UUID, body: CreateReferencedNfeRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.cte.issue")),
) -> ReferencedNfeResponse:
    handler = CreateReferencedNfeHandler()
    dto = await handler.handle(
        CreateReferencedNfeCommand(actor=actor, cte_id=cte_id, access_key=body.access_key)
    )
    return ReferencedNfeResponse.from_dto(dto)
