from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_employee_repository import (
    SqlAlchemyEmployeeRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeactivateEmployeeCommand(Command):
    actor: AuthenticatedActor
    employee_id: uuid.UUID


class DeactivateEmployeeHandler(CommandHandler[DeactivateEmployeeCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateEmployeeCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            employee_repo = SqlAlchemyEmployeeRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            employee = await employee_repo.get_by_id(command.employee_id)
            if employee is None:
                raise NotFoundError("IDENTITY_EMPLOYEE_NOT_FOUND", "Funcionário não encontrado.")

            if await user_repo.exists_active_linked_to_employee(command.employee_id):
                raise DomainError(
                    "IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER",
                    "Funcionário ainda vinculado a um Usuário ativo — desvincule ou desative o Usuário primeiro.",
                )

            employee.deactivate(deactivated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await employee_repo.add(employee)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="funcionarios",
                entidade_id=employee.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
