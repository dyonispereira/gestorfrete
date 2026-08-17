from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.delivery_status import DeliveryStatus
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
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
class UpdateDeliveryCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    delivery_id: uuid.UUID
    recipient: str | None
    delivery_address: dict[str, Any] | None
    status: DeliveryStatus | None
    rejection_reason: str | None


class UpdateDeliveryHandler(CommandHandler[UpdateDeliveryCommand, DeliveryDTO]):
    """D237 — quando a Entrega atinge estado terminal, o efeito no `Trip` (sub-ciclo multi-drop) é
    disparado pelo Domain aqui, nunca pelo Controller."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateDeliveryCommand) -> DeliveryDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)

            delivery = await delivery_repo.get_by_id(command.delivery_id)
            if delivery is None or delivery.viagem_id != command.trip_id:
                raise NotFoundError("FREIGHT_DELIVERY_NOT_FOUND", "Entrega não encontrada.")

            now = datetime.now(timezone.utc)
            was_terminal = delivery.is_terminal
            delivery.update(
                destinatario=command.recipient,
                endereco_entrega=command.delivery_address,
                status=command.status,
                rejection_reason=command.rejection_reason,
                now=now,
            )
            await delivery_repo.add(delivery)

            if delivery.is_terminal and not was_terminal:
                trip = await trip_repo.get_by_id(command.trip_id)
                if trip is not None:
                    remaining = await delivery_repo.count_pending_for_trip(command.trip_id, excluding_id=delivery.id)
                    reached = trip.on_delivery_terminal(has_pending_deliveries=remaining > 0)
                    if reached:
                        await trip_repo.add(trip)
                        for status in reached:
                            await history_repo.add(
                                TripStatusHistoryEntry.create(
                                    viagem_id=trip.id,
                                    dimensao=StatusHistoryDimension.OPERACIONAL,
                                    status=status.value,
                                    usuario_id=command.actor.user_id,
                                    origem="app_motorista",
                                    now=now,
                                )
                            )

            window = await delivery_repo.get_window(delivery.id)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="entregas",
                entidade_id=delivery.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": delivery.status.value},
            )

            await uow.commit()

        return DeliveryDTO.from_entity(delivery, window)
