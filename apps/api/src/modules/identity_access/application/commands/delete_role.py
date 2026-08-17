from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteRoleCommand(Command):
    actor: AuthenticatedActor
    role_id: uuid.UUID


class DeleteRoleHandler(CommandHandler[DeleteRoleCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteRoleCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            role_repo = SqlAlchemyRoleRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            role = await role_repo.get_by_id(command.role_id)
            if role is None:
                raise NotFoundError("IDENTITY_ROLE_NOT_FOUND", "Papel não encontrado.")

            if await role_repo.is_assigned_to_any_user(role.id):
                raise DomainError(
                    "IDENTITY_ROLE_IN_USE", "Papel ainda está atribuído a pelo menos um Usuário."
                )

            role.soft_delete(deleted_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await role_repo.add(role)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="papeis",
                entidade_id=role.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
            )

            await uow.commit()
