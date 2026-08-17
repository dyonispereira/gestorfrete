from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from core.security.password_hasher import BcryptPasswordHasher
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.domain.entities.user import User
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateUserCommand(Command):
    actor: AuthenticatedActor
    nome: str
    email: str
    password: str
    driver_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    role_ids: frozenset[uuid.UUID]


class CreateUserHandler(CommandHandler[CreateUserCommand, UserDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._hasher = BcryptPasswordHasher()

    async def handle(self, command: CreateUserCommand) -> UserDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            user_repo = SqlAlchemyUserRepository(uow.session)
            role_repo = SqlAlchemyRoleRepository(uow.session)

            if await user_repo.exists_with_email(command.email):
                raise ConflictError("IDENTITY_EMAIL_ALREADY_EXISTS", "E-mail já cadastrado neste tenant.")

            if command.role_ids:
                found = await role_repo.get_many(command.role_ids)
                missing = command.role_ids - {r.id for r in found}
                if missing:
                    raise ValidationError(
                        "IDENTITY_UNKNOWN_ROLE_ID", f"Papéis inexistentes: {sorted(str(m) for m in missing)}"
                    )

            now = datetime.now(timezone.utc)
            user = User.create(
                codigo=str(uuid.uuid4())[:8],
                nome=command.nome,
                email=command.email,
                senha_hash=self._hasher.hash(command.password),
                driver_id=command.driver_id,
                employee_id=command.employee_id,
                role_ids=command.role_ids,
                audit=AuditMetadata(created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id),
            )
            await user_repo.add(user)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="usuarios",
                entidade_id=user.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
                dados_depois={"nome": user.nome, "email": user.email, "role_ids": [str(r) for r in user.role_ids]},
            )

            await uow.commit()

        return UserDTO.from_entity(user)
