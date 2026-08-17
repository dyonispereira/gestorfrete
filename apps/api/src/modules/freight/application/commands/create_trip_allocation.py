from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, DomainError, NotFoundError, ValidationError
from modules.drivers.domain.value_objects.fitness_status import FitnessStatus
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.fleet.domain.value_objects.vehicle_status import VehicleStatus
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.freight.application.dtos.trip_allocation_dto import TripAllocationDTO
from modules.freight.domain.entities.trip_allocation import TripAllocation
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_allocation_repository import (
    SqlAlchemyTripAllocationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateTripAllocationCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    driver_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    implement_id: uuid.UUID | None


class CreateTripAllocationHandler(CommandHandler[CreateTripAllocationCommand, TripAllocationDTO]):
    """`POST /viagens/{id}/resources` — a **primeira** alocação (D188). Dispara
    `RASCUNHO→PLANEJADA` na mesma transação — para aí (não em cascata até `AGUARDANDO_CHECKLIST`),
    para a Viagem descansar observável em `PLANEJADA` e `commands/accept` (D129) fazer sentido."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateTripAllocationCommand) -> TripAllocationDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            allocation_repo = SqlAlchemyTripAllocationRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            implement_repo = SqlAlchemyImplementRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            if await allocation_repo.get_current_for_trip(command.trip_id) is not None:
                raise ConflictError(
                    "FREIGHT_TRIP_ALREADY_HAS_ALLOCATION",
                    "Viagem já possui uma alocação vigente — use commands/reallocate-resources.",
                )

            driver = await driver_repo.get_by_id(command.driver_id)
            if driver is None:
                raise ValidationError("FREIGHT_UNKNOWN_DRIVER_ID", "Motorista inexistente.")
            if driver.fitness_status == FitnessStatus.BLOQUEADO:
                raise DomainError("FREIGHT_DRIVER_NOT_FIT", "Motorista está bloqueado.")

            vehicle = await vehicle_repo.get_by_id(command.tractor_unit_id)
            if vehicle is None:
                raise ValidationError("FREIGHT_UNKNOWN_VEHICLE_ID", "Veículo Tracionador inexistente.")
            if vehicle.status != VehicleStatus.ATIVO:
                raise DomainError("FREIGHT_VEHICLE_UNAVAILABLE", "Veículo está inativo.")
            if await allocation_repo.exists_vigente_for_vehicle_excluding_trip(command.tractor_unit_id, command.trip_id):
                raise DomainError(
                    "FREIGHT_VEHICLE_UNAVAILABLE", "Veículo já está alocado como vigente em outra Viagem."
                )

            if command.implement_id is not None and await implement_repo.get_by_id(command.implement_id) is None:
                raise ValidationError("FREIGHT_UNKNOWN_IMPLEMENT_ID", "Implemento inexistente.")

            now = datetime.now(timezone.utc)
            allocation = TripAllocation.create(
                viagem_id=command.trip_id,
                motorista_id=command.driver_id,
                veiculo_tracionador_id=command.tractor_unit_id,
                implemento_id=command.implement_id,
                motivo_troca=None,
                now=now,
                created_by=command.actor.user_id,
            )
            await allocation_repo.add(allocation)

            trip.set_current_allocation(motorista_id=command.driver_id, veiculo_tracionador_id=command.tractor_unit_id)
            trip.plan()
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=command.actor.user_id,
                    origem="portal_gestor",
                    now=now,
                )
            )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="alocacoes_recurso_viagem",
                entidade_id=allocation.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"motorista_id": str(allocation.motorista_id), "veiculo_tracionador_id": str(allocation.veiculo_tracionador_id)},
            )

            await uow.commit()

        return TripAllocationDTO.from_entity(allocation)
