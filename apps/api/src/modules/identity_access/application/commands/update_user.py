from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateUserCommand(Command):
    actor: AuthenticatedActor
    user_id: uuid.UUID
    nome: str | None
    email: str | None
    role_ids: frozenset[uuid.UUID] | None


class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateUserCommand) -> UserDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            user_repo = SqlAlchemyUserRepository(uow.session)
            role_repo = SqlAlchemyRoleRepository(uow.session)

            user = await user_repo.get_by_id(command.user_id)
            if user is None:
                raise NotFoundError("IDENTITY_USER_NOT_FOUND", "Usuário não encontrado.")

            if command.email is not None and command.email != user.email:
                if await user_repo.exists_with_email(command.email):
                    raise ConflictError("IDENTITY_EMAIL_ALREADY_EXISTS", "E-mail já cadastrado.")

            if command.role_ids is not None:
                found = await role_repo.get_many(command.role_ids)
                missing = command.role_ids - {r.id for r in found}
                if missing:
                    raise ValidationError(
                        "IDENTITY_UNKNOWN_ROLE_ID", f"Papéis inexistentes: {sorted(str(m) for m in missing)}"
                    )

            before_roles = set(user.role_ids)
            now = datetime.now(timezone.utc)
            user.rename_and_update_email(
                nome=command.nome, email=command.email, updated_by=command.actor.user_id, now=now
            )
            if command.role_ids is not None:
                user.replace_roles(command.role_ids, updated_by=command.actor.user_id, now=now)

            await user_repo.add(user)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            if command.role_ids is not None and set(command.role_ids) != before_roles:
                await self._audit.record(
                    uow.session,
                    tenant_id=command.actor.tenant_id,
                    entidade_tipo="usuarios_papeis",
                    entidade_id=user.id,
                    acao="ALTERACAO",
                    ator_id=command.actor.user_id,
                    ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
                    dados_antes={"role_ids": sorted(str(r) for r in before_roles)},
                    dados_depois={"role_ids": sorted(str(r) for r in command.role_ids)},
                )
            else:
                await self._audit.record(
                    uow.session,
                    tenant_id=command.actor.tenant_id,
                    entidade_tipo="usuarios",
                    entidade_id=user.id,
                    acao="ALTERACAO",
                    ator_id=command.actor.user_id,
                    ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
                )

            await uow.commit()

        return UserDTO.from_entity(user)
