from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.domain.entities.delivery import Delivery
from modules.freight.domain.entities.delivery_window import DeliveryWindow
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateDeliveryCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    order: int
    recipient: str
    delivery_address: dict[str, Any]
    window_starts_at: datetime | None
    window_ends_at: datetime | None


class CreateDeliveryHandler(CommandHandler[CreateDeliveryCommand, DeliveryDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateDeliveryCommand) -> DeliveryDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)

            if await trip_repo.get_by_id(command.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            if await delivery_repo.exists_with_order(command.trip_id, command.order):
                raise ConflictError(
                    "FREIGHT_DELIVERY_ORDER_ALREADY_EXISTS", "Já existe uma Entrega com esta ordem nesta Viagem."
                )

            delivery = Delivery.create(
                viagem_id=command.trip_id,
                ordem=command.order,
                destinatario=command.recipient,
                endereco_entrega=command.delivery_address,
            )
            await delivery_repo.add(delivery)

            window: DeliveryWindow | None = None
            if command.window_starts_at is not None and command.window_ends_at is not None:
                window = DeliveryWindow.create(
                    entrega_id=delivery.id, hora_inicio=command.window_starts_at, hora_fim=command.window_ends_at
                )
                await delivery_repo.add_window(window)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="entregas",
                entidade_id=delivery.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"ordem": delivery.ordem, "destinatario": delivery.destinatario},
            )

            await uow.commit()

        return DeliveryDTO.from_entity(delivery, window)
