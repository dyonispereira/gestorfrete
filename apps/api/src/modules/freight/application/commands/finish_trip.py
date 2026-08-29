from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.delivery_status import DeliveryStatus
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_proof_of_delivery_repository import (
    SqlAlchemyProofOfDeliveryRepository,
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
class FinishTripCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class FinishTripHandler(CommandHandler[FinishTripCommand, TripDTO]):
    """`commands/finish` — pré-condição verificada aqui (Application), não pelo estado da máquina
    (D235): todas as Entregas em estado terminal, e toda Entrega `CONCLUIDA` com Canhoto
    `REGISTRADO`. Fecha o impedimento `VIAGEM` em `fleet` após o commit — libera o veículo em
    Disponibilidade só se nenhum outro impedimento (ex. uma OS aberta no mesmo veículo) continuar
    ativo (`VehicleAvailabilityProjector.apply_trip_ended`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: FinishTripCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)
            pod_repo = SqlAlchemyProofOfDeliveryRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            deliveries = await delivery_repo.list_for_trip(command.trip_id)
            for delivery in deliveries:
                if not delivery.is_terminal:
                    raise DomainError(
                        "FREIGHT_TRIP_DELIVERIES_PENDING", "Nem todas as Entregas estão em estado terminal."
                    )
                if delivery.status == DeliveryStatus.CONCLUIDA and not await pod_repo.exists_for_delivery(delivery.id):
                    raise DomainError(
                        "FREIGHT_TRIP_DELIVERIES_PENDING", "Existem Entregas concluídas sem Canhoto registrado."
                    )

            trip.finish()
            await trip_repo.add(trip)

            now = datetime.now(timezone.utc)
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
                entidade_tipo="viagens",
                entidade_id=trip.id,
                acao="TRANSICAO_STATUS",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status_operacional": trip.status_operacional.value},
            )

            await uow.commit()

        if trip.veiculo_tracionador_id is not None:
            await VehicleAvailabilityProjector().apply_trip_ended(
                vehicle_id=trip.veiculo_tracionador_id, trip_id=trip.id, at=now
            )

        return TripDTO.from_entity(trip)
