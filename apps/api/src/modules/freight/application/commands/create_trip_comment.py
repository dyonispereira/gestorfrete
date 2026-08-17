from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.session import get_session_factory
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from modules.identity_access.application.authorization_service import AuthorizationService
from shared.collaboration.domain.entities.comment import Comment
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_comment_repository import (
    SqlAlchemyCommentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateTripCommentCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    text: str
    visible_to_client: bool


class CreateTripCommentHandler(CommandHandler[CreateTripCommentCommand, Comment]):
    """`081-comments.md` — comentar exige só ver o dono (`freight.trip.view`/`.view_own`, checado
    pela rota) + `storage.comment.create` (checado aqui). `author_id` sempre da sessão, nunca do
    corpo (D295)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._authz = AuthorizationService(get_session_factory())

    async def handle(self, command: CreateTripCommentCommand) -> Comment:
        await self._authz.authorize(command.actor, "storage.comment.create")
        await GetTripHandler(get_session_factory()).handle(GetTripQuery(actor=command.actor, trip_id=command.trip_id))

        now = datetime.now(timezone.utc)
        comment = Comment.create(
            entidade_tipo="VIAGEM", entidade_id=command.trip_id, usuario_id=command.actor.user_id,
            texto=command.text, visivel_cliente=command.visible_to_client, now=now,
        )

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyCommentRepository(uow.session)
            await repo.create(comment)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="comentarios",
                entidade_id=comment.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"trip_id": str(command.trip_id)},
            )
            await uow.commit()

        return comment
