from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.drivers.application.commands.block_driver import BlockDriverCommand, BlockDriverHandler
from modules.drivers.application.commands.create_driver import CreateDriverCommand, CreateDriverHandler
from modules.drivers.application.commands.create_driver_document import (
    CreateDriverDocumentCommand,
    CreateDriverDocumentHandler,
)
from modules.drivers.application.commands.deactivate_driver import DeactivateDriverCommand, DeactivateDriverHandler
from modules.drivers.application.commands.delete_driver_document import (
    DeleteDriverDocumentCommand,
    DeleteDriverDocumentHandler,
)
from modules.drivers.application.commands.unblock_driver import UnblockDriverCommand, UnblockDriverHandler
from modules.drivers.application.commands.update_driver import UpdateDriverCommand, UpdateDriverHandler
from modules.drivers.application.commands.update_driver_document import (
    UpdateDriverDocumentCommand,
    UpdateDriverDocumentHandler,
)
from modules.drivers.application.queries.get_driver import GetDriverHandler, GetDriverQuery
from modules.drivers.application.queries.get_driver_document import GetDriverDocumentHandler, GetDriverDocumentQuery
from modules.drivers.application.queries.get_my_driver import GetMyDriverHandler, GetMyDriverQuery
from modules.drivers.application.queries.list_driver_documents import (
    ListDriverDocumentsHandler,
    ListDriverDocumentsQuery,
)
from modules.drivers.application.queries.list_drivers import ListDriversHandler, ListDriversQuery
from modules.drivers.domain.value_objects.cnh_category import CnhCategory
from modules.drivers.domain.value_objects.document_type import DocumentType
from modules.drivers.domain.value_objects.employment_type import EmploymentType
from modules.drivers.interfaces.schemas.driver_schemas import (
    CreateDriverDocumentRequest,
    CreateDriverRequest,
    DriverDocumentResponse,
    DriverResponse,
    UpdateDriverDocumentRequest,
    UpdateDriverRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("")
async def list_drivers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    employment_type: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.view")),
) -> dict[str, Any]:
    handler = ListDriversHandler(get_session_factory())
    result = await handler.handle(
        ListDriversQuery(
            actor=actor, page=page, limit=limit, status=status, employment_type=employment_type, search=search
        )
    )
    return {
        "data": [DriverResponse.from_dto(d) for d in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/me", response_model=DriverResponse)
async def get_my_driver(
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.view_own")),
) -> DriverResponse:
    """Registrado **antes** de `/drivers/{driver_id}` — caso contrário o FastAPI capturaria `"me"`
    como o path param `{driver_id}` e falharia a validação de UUID em vez de rotear aqui
    (`DRIVER_IMPLEMENTATION.md`)."""

    handler = GetMyDriverHandler(get_session_factory())
    dto = await handler.handle(GetMyDriverQuery(actor=actor))
    return DriverResponse.from_dto(dto)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.view")),
) -> DriverResponse:
    handler = GetDriverHandler(get_session_factory())
    dto = await handler.handle(GetDriverQuery(actor=actor, driver_id=driver_id))
    return DriverResponse.from_dto(dto)


@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(
    body: CreateDriverRequest,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.create")),
) -> DriverResponse:
    handler = CreateDriverHandler()
    dto = await handler.handle(
        CreateDriverCommand(
            actor=actor,
            nome=body.nome,
            cpf=body.cpf,
            telefone=body.telefone,
            email=body.email,
            employment_type=EmploymentType(body.employment_type),
        )
    )
    return DriverResponse.from_dto(dto)


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: uuid.UUID,
    body: UpdateDriverRequest,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.edit")),
) -> DriverResponse:
    handler = UpdateDriverHandler()
    dto = await handler.handle(
        UpdateDriverCommand(actor=actor, driver_id=driver_id, nome=body.nome, telefone=body.telefone, email=body.email)
    )
    return DriverResponse.from_dto(dto)


@router.post("/{driver_id}/block", response_model=DriverResponse)
async def block_driver(
    driver_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.block")),
) -> DriverResponse:
    handler = BlockDriverHandler()
    dto = await handler.handle(BlockDriverCommand(actor=actor, driver_id=driver_id))
    return DriverResponse.from_dto(dto)


@router.post("/{driver_id}/unblock", response_model=DriverResponse)
async def unblock_driver(
    driver_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.unblock")),
) -> DriverResponse:
    handler = UnblockDriverHandler()
    dto = await handler.handle(UnblockDriverCommand(actor=actor, driver_id=driver_id))
    return DriverResponse.from_dto(dto)


@router.delete("/{driver_id}", status_code=204, response_model=None)
async def deactivate_driver(
    driver_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.delete")),
) -> None:
    handler = DeactivateDriverHandler()
    await handler.handle(DeactivateDriverCommand(actor=actor, driver_id=driver_id))


# --- Documentos (D183) ---


@router.get("/{driver_id}/documents")
async def list_driver_documents(
    driver_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.view")),
) -> dict[str, Any]:
    handler = ListDriverDocumentsHandler(get_session_factory())
    documents = await handler.handle(ListDriverDocumentsQuery(actor=actor, driver_id=driver_id))
    return {
        "data": [DriverDocumentResponse.from_dto(d) for d in documents],
        "meta": {"pagination": {"page": 1, "limit": len(documents) or 1, "total": len(documents)}},
    }


@router.get("/{driver_id}/documents/{document_id}", response_model=DriverDocumentResponse)
async def get_driver_document(
    driver_id: uuid.UUID,
    document_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.view")),
) -> DriverDocumentResponse:
    handler = GetDriverDocumentHandler(get_session_factory())
    dto = await handler.handle(GetDriverDocumentQuery(actor=actor, driver_id=driver_id, document_id=document_id))
    return DriverDocumentResponse.from_dto(dto)


@router.post("/{driver_id}/documents", response_model=DriverDocumentResponse, status_code=201)
async def create_driver_document(
    driver_id: uuid.UUID,
    body: CreateDriverDocumentRequest,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.edit")),
) -> DriverDocumentResponse:
    # A permissão fina (CNH vs. demais) é resolvida de novo dentro do handler de negócio — a
    # dependency acima só garante o mínimo (`drivers.driver.edit`); ver nota em
    # `DRIVER_IMPLEMENTATION.md` sobre `view_cnh`/`edit_cnh` serem checados a partir do `type` do
    # corpo da requisição, não do path (não dá para saber o tipo antes de o FastAPI ler o corpo).
    handler = CreateDriverDocumentHandler()
    dto = await handler.handle(
        CreateDriverDocumentCommand(
            actor=actor,
            driver_id=driver_id,
            tipo_documento=DocumentType(body.type),
            numero=body.number,
            categoria_cnh=CnhCategory(body.cnh_category) if body.cnh_category else None,
            data_validade=body.expires_at,
            arquivo_id=None,
        )
    )
    return DriverDocumentResponse.from_dto(dto)


@router.patch("/{driver_id}/documents/{document_id}", response_model=DriverDocumentResponse)
async def update_driver_document(
    driver_id: uuid.UUID,
    document_id: uuid.UUID,
    body: UpdateDriverDocumentRequest,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.edit")),
) -> DriverDocumentResponse:
    handler = UpdateDriverDocumentHandler()
    dto = await handler.handle(
        UpdateDriverDocumentCommand(
            actor=actor,
            driver_id=driver_id,
            document_id=document_id,
            numero=body.number,
            categoria_cnh=CnhCategory(body.cnh_category) if body.cnh_category else None,
            data_validade=body.expires_at,
            arquivo_id=None,
        )
    )
    return DriverDocumentResponse.from_dto(dto)


@router.delete("/{driver_id}/documents/{document_id}", status_code=204, response_model=None)
async def delete_driver_document(
    driver_id: uuid.UUID,
    document_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("drivers.driver.edit")),
) -> None:
    handler = DeleteDriverDocumentHandler()
    await handler.handle(DeleteDriverDocumentCommand(actor=actor, driver_id=driver_id, document_id=document_id))
