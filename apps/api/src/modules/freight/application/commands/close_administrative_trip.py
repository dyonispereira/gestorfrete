from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.freight.application.dtos.trip_dto import TripDTO
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
class CloseAdministrativeTripCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    justification: str


class CloseAdministrativeTripHandler(CommandHandler[CloseAdministrativeTripCommand, TripDTO]):
    """`commands/close-administrative` — exceção documentada (`002-VIAGEM.md`), nunca a via normal
    de `FINALIZADA`. **Nunca** força `viagens.encerrada` (a coluna `GENERATED`) — a convergência
    continua exigindo Fiscal/Financeiro reais (D019). Fecha o impedimento `VIAGEM` em `fleet` após
    o commit, mesmo padrão de `finish_trip.py`. V1 Operational Hardening, Parte 1 — encerra a
    Alocação `VIGENTE` (se existir) na mesma transação (→ `AllocationStatus.ENCERRADA`, sem relação
    com `viagens.encerrada` apesar do nome parecido), para que o Veículo volte a ser alocável."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CloseAdministrativeTripCommand) -> TripDTO:
        if not command.justification or not command.justification.strip():
            raise ValidationError(
                "FREIGHT_TRIP_JUSTIFICATION_REQUIRED", "justification é obrigatória para encerramento administrativo."
            )

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            allocation_repo = SqlAlchemyTripAllocationRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            trip.close_administrative()
            await trip_repo.add(trip)

            current_allocation = await allocation_repo.get_current_for_trip(trip.id)
            if current_allocation is not None:
                current_allocation.end()
                await allocation_repo.add(current_allocation)

            now = datetime.now(timezone.utc)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=command.actor.user_id,
                    origem="portal_gestor",
                    now=now,
                    observacao=command.justification,
                )
            )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="viagens",
                entidade_id=trip.id,
                acao="TRANSICAO_STATUS",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                motivo=command.justification,
            )

            await uow.commit()

        if trip.veiculo_tracionador_id is not None:
            await VehicleAvailabilityProjector().apply_trip_ended(
                vehicle_id=trip.veiculo_tracionador_id, trip_id=trip.id, at=now
            )

        return TripDTO.from_entity(trip)
