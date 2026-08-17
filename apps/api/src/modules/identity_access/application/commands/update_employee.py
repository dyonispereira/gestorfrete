from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.identity_access.application.dtos.employee_dto import EmployeeDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_employee_repository import (
    SqlAlchemyEmployeeRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateEmployeeCommand(Command):
    actor: AuthenticatedActor
    employee_id: uuid.UUID
    nome: str | None
    cargo: str | None
    data_admissao: date | None


class UpdateEmployeeHandler(CommandHandler[UpdateEmployeeCommand, EmployeeDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateEmployeeCommand) -> EmployeeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyEmployeeRepository(uow.session)

            employee = await repo.get_by_id(command.employee_id)
            if employee is None:
                raise NotFoundError("IDENTITY_EMPLOYEE_NOT_FOUND", "Funcionário não encontrado.")

            employee.update(
                nome=command.nome,
                cargo=command.cargo,
                data_admissao=command.data_admissao,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(employee)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="funcionarios",
                entidade_id=employee.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return EmployeeDTO.from_entity(employee)
