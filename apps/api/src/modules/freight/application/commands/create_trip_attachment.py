from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.session import get_session_factory
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.storage.application.queries.get_file import GetFileHandler, GetFileQuery
from shared.collaboration.domain.entities.attachment import Attachment
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateTripAttachmentCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    attachment_type: str
    file_id: uuid.UUID
    description: str | None


class CreateTripAttachmentHandler(CommandHandler[CreateTripAttachmentCommand, Attachment]):
    """`080-attachments.md` — dono sempre resolvido pelo path (`Viagem`), nunca por campo do corpo
    (D316). Exige `freight.trip.edit` (checado pela rota) **e** `storage.attachment.create`
    (checado aqui, já que uma rota só resolve uma permissão via `require_permission`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._authz = AuthorizationService(get_session_factory())

    async def handle(self, command: CreateTripAttachmentCommand) -> Attachment:
        await self._authz.authorize(command.actor, "storage.attachment.create")

        # Confere que o dono existe (404 se não) e que o File referenciado está ATIVO (404 se não).
        await GetTripHandler(get_session_factory()).handle(GetTripQuery(actor=command.actor, trip_id=command.trip_id))
        file_dto = await GetFileHandler(get_session_factory()).handle(
            GetFileQuery(actor=command.actor, file_id=command.file_id)
        )
        if file_dto.status != "ATIVO":
            raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")

        now = datetime.now(timezone.utc)
        attachment = Attachment.create(
            entidade_tipo="VIAGEM", entidade_id=command.trip_id, tipo_anexo=command.attachment_type,
            arquivo_id=command.file_id, descricao=command.description, now=now, created_by=command.actor.user_id,
        )

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAttachmentRepository(uow.session)
            await repo.create(attachment)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="anexos", entidade_id=attachment.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"trip_id": str(command.trip_id), "attachment_type": command.attachment_type},
            )
            await uow.commit()

        return attachment
