from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.fleet.application.dtos.odometer_reading_dto import OdometerReadingDTO
from modules.fleet.domain.entities.odometer_reading import OdometerReading
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_odometer_reading_repository import (
    SqlAlchemyOdometerReadingRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RegisterOdometerReadingCommand(Command):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    value_km: Decimal
    origin: OdometerOrigin
    trip_id: uuid.UUID | None


class RegisterOdometerReadingHandler(CommandHandler[RegisterOdometerReadingCommand, OdometerReadingDTO]):
    """Invariante "hodômetro nunca decresce" (D365) — validação de Application, não trigger:
    busca a última leitura do veículo dentro da mesma UoW antes de inserir
    (`ODOMETER_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RegisterOdometerReadingCommand) -> OdometerReadingDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            if await vehicle_repo.get_by_id(command.vehicle_id) is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            reading_repo = SqlAlchemyOdometerReadingRepository(uow.session)
            latest = await reading_repo.get_latest_for_vehicle(command.vehicle_id)
            if latest is not None and command.value_km < latest.valor_km:
                raise DomainError(
                    "FLEET_ODOMETER_READING_LOWER_THAN_LAST",
                    f"Leitura ({command.value_km}km) menor que a última registrada ({latest.valor_km}km) para este veículo.",
                )

            reading = OdometerReading.create(
                veiculo_tracionador_id=command.vehicle_id,
                valor_km=command.value_km,
                origem=command.origin,
                viagem_id=command.trip_id,
                now=datetime.now(timezone.utc),
            )
            await reading_repo.add(reading)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="leituras_hodometro",
                entidade_id=reading.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"valor_km": str(reading.valor_km), "origem": reading.origem.value},
            )

            await uow.commit()

        return OdometerReadingDTO.from_entity(reading)
