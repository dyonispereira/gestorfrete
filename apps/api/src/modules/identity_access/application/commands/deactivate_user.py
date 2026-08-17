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

ADMIN_ROLE_CODE = "ADMINISTRADOR_EMPRESA"
"""Vocabulário de código de Papel considerado "Administrador" para a regra
`IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN` (`003-users.md`) — mesmo código usado por `SEED_DATA.md`
para o Tenant Bootstrap (`RBAC_MATRIX.md` seção 9, hierarquia Administrador/Diretor/.../Operacional).
"""


@dataclass(frozen=True)
class DeactivateUserCommand(Command):
    actor: AuthenticatedActor
    user_id: uuid.UUID


class DeactivateUserHandler(CommandHandler[DeactivateUserCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateUserCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            user_repo = SqlAlchemyUserRepository(uow.session)
            role_repo = SqlAlchemyRoleRepository(uow.session)

            user = await user_repo.get_by_id(command.user_id)
            if user is None:
                raise NotFoundError("IDENTITY_USER_NOT_FOUND", "Usuário não encontrado.")

            admin_roles, _ = await role_repo.list_page(page=1, limit=1000, search=None)
            admin_role_ids = frozenset(r.id for r in admin_roles if r.codigo == ADMIN_ROLE_CODE)
            if admin_role_ids & user.role_ids:
                remaining_admins = await user_repo.count_active_admins(
                    excluding_user_id=user.id, admin_role_ids=admin_role_ids
                )
                if remaining_admins == 0:
                    raise DomainError(
                        "IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN",
                        "Não é possível desativar o último Usuário Administrador do tenant.",
                    )

            user.deactivate(deactivated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await user_repo.add(user)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="usuarios",
                entidade_id=user.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
            )

            await uow.commit()
