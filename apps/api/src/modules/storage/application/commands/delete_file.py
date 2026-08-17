from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteFileCommand(Command):
    actor: AuthenticatedActor
    file_id: uuid.UUID


class DeleteFileHandler(CommandHandler[DeleteFileCommand, None]):
    """D219 — soft delete; objeto físico intocado. `409 STORAGE_FILE_IN_USE` se referenciado por um
    Attachment ativo (`080-attachments.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteFileCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            file_repo = SqlAlchemyFileRepository(uow.session)
            attachment_repo = SqlAlchemyAttachmentRepository(uow.session)

            file = await file_repo.get_by_id(command.file_id)
            if file is None:
                raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")

            if await attachment_repo.count_by_file_id(command.file_id) > 0:
                raise ConflictError("STORAGE_FILE_IN_USE", "Arquivo referenciado por um Anexo ativo.")

            file.mark_deleted()
            await file_repo.add(file)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="arquivos", entidade_id=file.id,
                acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
