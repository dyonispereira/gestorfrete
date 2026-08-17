from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.storage.domain.entities.file import File


@dataclass(frozen=True)
class FileDTO:
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
    def from_entity(file: File) -> "FileDTO":
        return FileDTO(
            id=file.id, name=file.nome_original, mime_type=file.tipo_mime, size_bytes=file.tamanho_bytes,
            hash=file.hash_sha256, version=file.versao, previous_file_id=file.arquivo_anterior_id,
            origin=file.origem.value, status=file.status.value, created_at=file.criado_em,
        )
