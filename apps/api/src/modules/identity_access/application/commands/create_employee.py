from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.identity_access.application.dtos.employee_dto import EmployeeDTO
from modules.identity_access.domain.entities.employee import Employee
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_employee_repository import (
    SqlAlchemyEmployeeRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateEmployeeCommand(Command):
    actor: AuthenticatedActor
    nome: str
    cargo: str
    data_admissao: date | None


class CreateEmployeeHandler(CommandHandler[CreateEmployeeCommand, EmployeeDTO]):
    """Sem checagem de unicidade — `funcionarios` não tem `UNIQUE` além de `(tenant_id, codigo)`
    gerado pela aplicação (`EMPLOYEE_IMPLEMENTATION.md`, observação de `010-employees.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateEmployeeCommand) -> EmployeeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyEmployeeRepository(uow.session)

            now = datetime.now(timezone.utc)
            employee = Employee.create(
                codigo=str(uuid.uuid4())[:8],
                nome=command.nome,
                cargo=command.cargo,
                data_admissao=command.data_admissao,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(employee)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="funcionarios",
                entidade_id=employee.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"nome": employee.nome, "cargo": employee.cargo},
            )

            await uow.commit()

        return EmployeeDTO.from_entity(employee)
