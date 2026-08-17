from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError, ValidationError
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.freight.application.dtos.trip_allocation_dto import TripAllocationDTO
from modules.freight.domain.entities.trip_allocation import TripAllocation
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_allocation_repository import (
    SqlAlchemyTripAllocationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ALLOCATABLE_STATUSES = frozenset(
    {
        TripOperationalStatus.PLANEJADA,
        TripOperationalStatus.AGUARDANDO_CHECKLIST,
        TripOperationalStatus.LIBERADA,
        TripOperationalStatus.EM_DESLOCAMENTO,
        TripOperationalStatus.CARREGANDO,
        TripOperationalStatus.EM_TRANSITO,
        TripOperationalStatus.EM_ENTREGA,
    }
)


@dataclass(frozen=True)
class ReallocateTripResourcesCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    driver_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    implement_id: uuid.UUID | None
    reason: str


class ReallocateTripResourcesHandler(CommandHandler[ReallocateTripResourcesCommand, TripAllocationDTO]):
    """`commands/reallocate-resources` — "Troca de cavalo"/"Troca de motorista" (`002-VIAGEM.md`).
    A `VIGENTE` atual vira `SUBSTITUIDA` (imutável a partir daí); nunca edita a linha antiga."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ReallocateTripResourcesCommand) -> TripAllocationDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            allocation_repo = SqlAlchemyTripAllocationRepository(uow.session)
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            implement_repo = SqlAlchemyImplementRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            if trip.status_operacional not in _ALLOCATABLE_STATUSES:
                raise DomainError(
                    "FREIGHT_TRIP_NOT_ALLOCATABLE", "Viagem fora da janela PLANEJADA–EM_ENTREGA para realocação."
                )

            current = await allocation_repo.get_current_for_trip(command.trip_id)
            if current is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem ainda não tem alocação vigente.")

            if await driver_repo.get_by_id(command.driver_id) is None:
                raise ValidationError("FREIGHT_UNKNOWN_DRIVER_ID", "Motorista inexistente.")
            if await vehicle_repo.get_by_id(command.tractor_unit_id) is None:
                raise ValidationError("FREIGHT_UNKNOWN_VEHICLE_ID", "Veículo Tracionador inexistente.")
            if command.implement_id is not None and await implement_repo.get_by_id(command.implement_id) is None:
                raise ValidationError("FREIGHT_UNKNOWN_IMPLEMENT_ID", "Implemento inexistente.")

            current.supersede()
            await allocation_repo.add(current)

            now = datetime.now(timezone.utc)
            new_allocation = TripAllocation.create(
                viagem_id=command.trip_id,
                motorista_id=command.driver_id,
                veiculo_tracionador_id=command.tractor_unit_id,
                implemento_id=command.implement_id,
                motivo_troca=command.reason,
                now=now,
                created_by=command.actor.user_id,
            )
            await allocation_repo.add(new_allocation)

            trip.set_current_allocation(motorista_id=command.driver_id, veiculo_tracionador_id=command.tractor_unit_id)
            await trip_repo.add(trip)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="alocacoes_recurso_viagem",
                entidade_id=new_allocation.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                motivo=command.reason,
            )

            await uow.commit()

        return TripAllocationDTO.from_entity(new_allocation)
