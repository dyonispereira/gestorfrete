from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.storage.application.dtos.file_dto import FileDTO


class InitiateUploadRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    mime_type: str
    size_bytes: int
    origin: str
    previous_file_id: uuid.UUID | None = None


class InitiateUploadResponse(BaseModel):
    file_id: uuid.UUID
    upload_url: str
    expires_at: datetime


class FileResponse(BaseModel):
    id: uuid.UUID
    name: str
    mime_type: str
    size_bytes: int
    hash: str
    version: int
    previous_file_id: uuid.UUID | None
    origin: str
    status: str
    created_at: datetime

    @staticmethod
    def from_dto(dto: FileDTO) -> "FileResponse":
        return FileResponse(
            id=dto.id, name=dto.name, mime_type=dto.mime_type, size_bytes=dto.size_bytes, hash=dto.hash,
            version=dto.version, previous_file_id=dto.previous_file_id, origin=dto.origin, status=dto.status,
            created_at=dto.created_at,
        )


class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_at: datetime
