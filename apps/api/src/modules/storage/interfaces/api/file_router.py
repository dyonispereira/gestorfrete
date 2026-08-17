from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.storage.application.commands.complete_file_upload import (
    CompleteFileUploadCommand,
    CompleteFileUploadHandler,
)
from modules.storage.application.commands.delete_file import DeleteFileCommand, DeleteFileHandler
from modules.storage.application.commands.upload_file import UploadFileCommand, UploadFileHandler
from modules.storage.application.queries.get_file import GetFileHandler, GetFileQuery
from modules.storage.application.queries.get_file_download_url import (
    GetFileDownloadUrlHandler,
    GetFileDownloadUrlQuery,
)
from modules.storage.application.queries.list_file_versions import ListFileVersionsHandler, ListFileVersionsQuery
from modules.storage.application.queries.list_files import ListFilesHandler, ListFilesQuery
from modules.storage.domain.value_objects.file_origin import FileOrigin
from modules.storage.interfaces.schemas.file_schemas import (
    DownloadUrlResponse,
    FileResponse,
    InitiateUploadRequest,
    InitiateUploadResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.post("/uploads", response_model=InitiateUploadResponse, status_code=201)
async def initiate_upload(
    body: InitiateUploadRequest, actor: AuthenticatedActor = Depends(require_permission("storage.file.upload"))
) -> InitiateUploadResponse:
    handler = UploadFileHandler()
    result = await handler.handle(
        UploadFileCommand(
            actor=actor, name=body.name, mime_type=body.mime_type, size_bytes=body.size_bytes,
            origin=FileOrigin(body.origin), previous_file_id=body.previous_file_id,
        )
    )
    return InitiateUploadResponse(file_id=result.file_id, upload_url=result.upload_url, expires_at=result.expires_at)


@router.post("/uploads/{file_id}/commands/complete", response_model=FileResponse)
async def complete_upload(
    file_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("storage.file.upload"))
) -> FileResponse:
    handler = CompleteFileUploadHandler()
    dto = await handler.handle(CompleteFileUploadCommand(actor=actor, file_id=file_id))
    return FileResponse.from_dto(dto)


@router.get("/files")
async def list_files(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    mime_type: str | None = None,
    origin: str | None = None,
    status: str = "ATIVO",
    actor: AuthenticatedActor = Depends(require_permission("storage.file.view")),
) -> dict[str, Any]:
    handler = ListFilesHandler(get_session_factory())
    result = await handler.handle(
        ListFilesQuery(actor=actor, page=page, limit=limit, mime_type=mime_type, origin=origin, status=status)
    )
    return {
        "data": [FileResponse.from_dto(f) for f in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("storage.file.view"))
) -> FileResponse:
    handler = GetFileHandler(get_session_factory())
    dto = await handler.handle(GetFileQuery(actor=actor, file_id=file_id))
    return FileResponse.from_dto(dto)


@router.get("/files/{file_id}/versions")
async def list_file_versions(
    file_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("storage.file.view"))
) -> dict[str, Any]:
    handler = ListFileVersionsHandler(get_session_factory())
    versions = await handler.handle(ListFileVersionsQuery(actor=actor, file_id=file_id))
    return {
        "data": [FileResponse.from_dto(v) for v in versions],
        "meta": {"pagination": {"page": 1, "limit": len(versions), "total": len(versions)}},
    }


@router.get("/files/{file_id}/download-url", response_model=DownloadUrlResponse)
async def get_file_download_url(
    file_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("storage.file.view"))
) -> DownloadUrlResponse:
    handler = GetFileDownloadUrlHandler(get_session_factory())
    result = await handler.handle(GetFileDownloadUrlQuery(actor=actor, file_id=file_id))
    return DownloadUrlResponse(download_url=result.download_url, expires_at=result.expires_at)


@router.delete("/files/{file_id}", status_code=204, response_model=None)
async def delete_file(
    file_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("storage.file.delete"))
) -> None:
    handler = DeleteFileHandler()
    await handler.handle(DeleteFileCommand(actor=actor, file_id=file_id))
