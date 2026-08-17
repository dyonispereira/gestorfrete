from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.session import get_session_factory
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from modules.identity_access.application.authorization_service import AuthorizationService
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteTripAttachmentCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    attachment_id: uuid.UUID


class DeleteTripAttachmentHandler(CommandHandler[DeleteTripAttachmentCommand, None]):
    """Hard delete real — remove só o vínculo (`anexos`), o `File` permanece intacto (`080`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._authz = AuthorizationService(get_session_factory())

    async def handle(self, command: DeleteTripAttachmentCommand) -> None:
        await self._authz.authorize(command.actor, "storage.attachment.delete")
        await GetTripHandler(get_session_factory()).handle(GetTripQuery(actor=command.actor, trip_id=command.trip_id))

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAttachmentRepository(uow.session)
            attachment = await repo.get_by_id(command.attachment_id)
            if (
                attachment is None
                or attachment.entidade_tipo != "VIAGEM"
                or attachment.entidade_id != command.trip_id
            ):
                raise NotFoundError("STORAGE_ATTACHMENT_NOT_FOUND", "Anexo não encontrado.")

            await repo.delete(command.attachment_id)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="anexos",
                entidade_id=command.attachment_id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
