from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from modules.identity_access.application.dtos.role_dto import RoleDTO
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


@dataclass(frozen=True)
class UpdateRoleCommand(Command):
    actor: AuthenticatedActor
    role_id: uuid.UUID
    nome: str | None
    descricao: str | None
    permission_codes: list[str] | None


class UpdateRoleHandler(CommandHandler[UpdateRoleCommand, RoleDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateRoleCommand) -> RoleDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            role_repo = SqlAlchemyRoleRepository(uow.session)
            permission_repo = SqlAlchemyPermissionRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            role = await role_repo.get_by_id(command.role_id)
            if role is None:
                raise NotFoundError("IDENTITY_ROLE_NOT_FOUND", "Papel não encontrado.")

            if command.nome is not None and command.nome != role.nome:
                if await role_repo.exists_with_name(command.nome, excluding_id=role.id):
                    raise ConflictError("IDENTITY_ROLE_NAME_ALREADY_EXISTS", "Nome já em uso.")

            permission_ids = None
            if command.permission_codes is not None:
                permissions = await permission_repo.get_by_codes(command.permission_codes)
                found_codes = {p.code for p in permissions}
                unknown = set(command.permission_codes) - found_codes
                if unknown:
                    raise ValidationError(
                        "IDENTITY_UNKNOWN_PERMISSION_CODE", f"Códigos inexistentes: {sorted(unknown)}"
                    )
                permission_ids = frozenset(p.id for p in permissions)

            role.update(
                nome=command.nome,
                descricao=command.descricao,
                permission_ids=permission_ids,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await role_repo.add(role)

            actor_user = await user_repo.get_by_id(command.actor.user_id)
            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="papeis",
                entidade_id=role.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=actor_user.nome if actor_user else str(command.actor.user_id),
                dados_depois={"nome": role.nome, "permission_ids": sorted(str(p) for p in role.permission_ids)},
            )

            await uow.commit()

            # Fonte da verdade final: os códigos por trás de `role.permission_ids` já persistidos,
            # resolvidos ainda dentro da mesma sessão (evita uma segunda conexão só para isso).
            final_permissions = await permission_repo.get_by_ids(role.permission_ids)

        return RoleDTO.from_entity(role, [p.code for p in final_permissions])
