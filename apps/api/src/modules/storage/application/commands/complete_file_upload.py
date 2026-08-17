from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.storage.application.dtos.file_dto import FileDTO
from modules.storage.infrastructure.object_storage import compute_object_hash, stat_object
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CompleteFileUploadCommand(Command):
    actor: AuthenticatedActor
    file_id: uuid.UUID


class CompleteFileUploadHandler(CommandHandler[CompleteFileUploadCommand, FileDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CompleteFileUploadCommand) -> FileDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            file_repo = SqlAlchemyFileRepository(uow.session)
            file = await file_repo.get_by_id(command.file_id)
            if file is None:
                raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")

            size_bytes = await stat_object(file.storage_key)
            if size_bytes is None:
                raise ConflictError(
                    "STORAGE_UPLOAD_NOT_FOUND_IN_PROVIDER", "Binário ainda não chegou ao Storage."
                )
            hash_sha256 = await compute_object_hash(file.storage_key)

            file.confirm(tamanho_bytes=size_bytes, hash_sha256=hash_sha256)
            await file_repo.add(file)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="arquivos", entidade_id=file.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"hash": hash_sha256, "size_bytes": size_bytes},
            )
            await uow.commit()

        return FileDTO.from_entity(file)
