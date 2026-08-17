from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.drivers.domain.entities.driver import Driver
from modules.drivers.domain.value_objects.employment_type import EmploymentType
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateDriverCommand(Command):
    actor: AuthenticatedActor
    nome: str
    cpf: str
    telefone: str | None
    email: str | None
    employment_type: EmploymentType


class CreateDriverHandler(CommandHandler[CreateDriverCommand, DriverDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateDriverCommand) -> DriverDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDriverRepository(uow.session)

            if await repo.exists_with_cpf(command.cpf):
                raise ConflictError("DRIVERS_CPF_ALREADY_EXISTS", "Já existe um Motorista com este CPF neste tenant.")

            now = datetime.now(timezone.utc)
            driver = Driver.create(
                codigo=str(uuid.uuid4())[:8],
                nome=command.nome,
                cpf=command.cpf,
                telefone=command.telefone,
                email=command.email,
                employment_type=command.employment_type,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(driver)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="motoristas",
                entidade_id=driver.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"nome": driver.nome, "cpf": driver.cpf},
            )

            await uow.commit()

        return DriverDTO.from_entity(driver)
