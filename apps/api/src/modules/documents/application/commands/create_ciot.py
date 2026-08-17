from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, ValidationError
from modules.documents.application.dtos.ciot_dto import CiotDTO
from modules.documents.domain.entities.ciot import Ciot
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_repository import (
    SqlAlchemyCiotRepository,
)
from modules.drivers.domain.value_objects.employment_type import EmploymentType
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateCiotCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    driver_id: uuid.UUID


class CreateCiotHandler(CommandHandler[CreateCiotCommand, CiotDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateCiotCommand) -> CiotDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            ciot_repo = SqlAlchemyCiotRepository(uow.session)

            if await trip_repo.get_by_id(command.trip_id) is None:
                raise ValidationError("FISCAL_UNKNOWN_TRIP_ID", "Viagem inexistente.")

            driver = await driver_repo.get_by_id(command.driver_id)
            if driver is None:
                raise ValidationError("FISCAL_UNKNOWN_DRIVER_ID", "Motorista inexistente.")
            if driver.employment_type != EmploymentType.AUTONOMO:
                raise DomainError(
                    "FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS", "CIOT só se aplica a motorista com vínculo AUTONOMO."
                )

            ciot = Ciot.create(viagem_id=command.trip_id, motorista_id=command.driver_id)
            await ciot_repo.add(ciot)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ciots", entidade_id=ciot.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"viagem_id": str(ciot.viagem_id), "motorista_id": str(ciot.motorista_id)},
            )
            await uow.commit()

        return CiotDTO.from_entity(ciot)
