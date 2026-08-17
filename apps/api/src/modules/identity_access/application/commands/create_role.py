from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.identity_access.application.dtos.role_dto import RoleDTO
from modules.identity_access.domain.entities.role import Role
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
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
class CreateRoleCommand(Command):
    actor: AuthenticatedActor
    nome: str
    descricao: str | None
    permission_codes: list[str]


class CreateRoleHandler(CommandHandler[CreateRoleCommand, RoleDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateRoleCommand) -> RoleDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            role_repo = SqlAlchemyRoleRepository(uow.session)
            permission_repo = SqlAlchemyPermissionRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            if await role_repo.exists_with_name(command.nome):
                raise ConflictError("IDENTITY_ROLE_NAME_ALREADY_EXISTS", "Já existe um Papel com esse nome.")

            # D216 aplicado em runtime — todo código precisa existir em RBAC_MATRIX.md/`permissoes`.
            permissions = await permission_repo.get_by_codes(command.permission_codes)
            found_codes = {p.code for p in permissions}
            unknown = set(command.permission_codes) - found_codes
            if unknown:
                raise ValidationError(
                    "IDENTITY_UNKNOWN_PERMISSION_CODE", f"Códigos inexistentes: {sorted(unknown)}"
                )

            now = datetime.now(timezone.utc)
            role = Role.create(
                codigo=str(uuid.uuid4())[:8],
                nome=command.nome,
                descricao=command.descricao,
                permission_ids=frozenset(p.id for p in permissions),
                audit=AuditMetadata(created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id),
            )
            await role_repo.add(role)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="papeis",
                entidade_id=role.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
                dados_depois={"nome": role.nome, "permissions": sorted(command.permission_codes)},
            )

            await uow.commit()

        return RoleDTO.from_entity(role, [p.code for p in permissions])
