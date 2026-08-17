from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.storage.domain.entities.file import File
from modules.storage.domain.value_objects.file_origin import FileOrigin
from modules.storage.infrastructure.object_storage import (
    UPLOAD_URL_EXPIRY,
    build_storage_key,
    ensure_bucket_exists,
    presigned_upload_url,
)
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UploadFileCommand(Command):
    actor: AuthenticatedActor
    name: str
    mime_type: str
    size_bytes: int
    origin: FileOrigin
    previous_file_id: uuid.UUID | None


@dataclass(frozen=True)
class UploadFileResultDTO:
    file_id: uuid.UUID
    upload_url: str
    expires_at: datetime


class UploadFileHandler(CommandHandler[UploadFileCommand, UploadFileResultDTO]):
    """`POST /storage/uploads` — D415: materializa a linha `arquivos` já aqui (status `ATIVO`), já
    que o enum não tem um valor intermediário; `commands/complete` confirma/corrige."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UploadFileCommand) -> UploadFileResultDTO:
        await ensure_bucket_exists()

        async with SQLAlchemyUnitOfWork() as uow:
            file_repo = SqlAlchemyFileRepository(uow.session)

            versao = 1
            if command.previous_file_id is not None:
                previous = await file_repo.get_by_id(command.previous_file_id)
                if previous is None:
                    raise NotFoundError("STORAGE_PREVIOUS_FILE_NOT_FOUND", "Versão anterior não encontrada.")
                versao = previous.versao + 1

            now = datetime.now(timezone.utc)
            file = File.declare(
                nome_original=command.name, tipo_mime=command.mime_type, tamanho_bytes=command.size_bytes,
                origem=command.origin, storage_key="", versao=versao, arquivo_anterior_id=command.previous_file_id,
                now=now, created_by=command.actor.user_id,
            )
            file.storage_key = build_storage_key(command.actor.tenant_id, file.id)
            await file_repo.add(file)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="arquivos", entidade_id=file.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"name": command.name, "mime_type": command.mime_type},
            )
            await uow.commit()

        upload_url = await presigned_upload_url(file.storage_key)
        return UploadFileResultDTO(
            file_id=file.id, upload_url=upload_url, expires_at=now + UPLOAD_URL_EXPIRY
        )
