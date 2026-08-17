from __future__ import annotations

from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.identity_access.domain.value_objects.enums import SessionEndedReason
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class LogoutCommand(Command):
    actor: AuthenticatedActor


class LogoutHandler(CommandHandler[LogoutCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: LogoutCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            session_repo = SqlAlchemySessionRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            session = await session_repo.get_by_id(command.actor.session_id)
            if session is not None:
                session.end(SessionEndedReason.LOGOUT)
                await session_repo.add(session)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="sessoes_acesso",
                entidade_id=command.actor.session_id,
                acao="LOGOUT",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
            )

            await uow.commit()
