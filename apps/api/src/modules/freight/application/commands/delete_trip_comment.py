from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_comment_repository import (
    SqlAlchemyCommentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteTripCommentCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    comment_id: uuid.UUID


class DeleteTripCommentHandler(CommandHandler[DeleteTripCommentCommand, None]):
    """Hard delete real — só o próprio autor exclui (`081-comments.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteTripCommentCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyCommentRepository(uow.session)
            comment = await repo.get_by_id(command.comment_id)
            if comment is None or comment.entidade_tipo != "VIAGEM" or comment.entidade_id != command.trip_id:
                raise NotFoundError("STORAGE_COMMENT_NOT_FOUND", "Comentário não encontrado.")
            if comment.usuario_id != command.actor.user_id:
                raise AuthorizationError("STORAGE_COMMENT_NOT_OWNED", "Só o próprio autor exclui o comentário.")

            await repo.delete(command.comment_id)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="comentarios",
                entidade_id=command.comment_id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
