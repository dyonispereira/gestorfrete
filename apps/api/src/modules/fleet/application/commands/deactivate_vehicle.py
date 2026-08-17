from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeactivateVehicleCommand(Command):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID


class DeactivateVehicleHandler(CommandHandler[DeactivateVehicleCommand, None]):
    """`FLEET_VEHICLE_HAS_ACTIVE_TRIP` (422) não é checado aqui — depende de
    `alocacoes_recurso_viagem`/`freight`, ainda não implementado (Lote 5+). Soft delete
    incondicional por enquanto (`VEHICLE_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateVehicleCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleRepository(uow.session)

            vehicle = await repo.get_by_id(command.vehicle_id)
            if vehicle is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            vehicle.deactivate(deactivated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(vehicle)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="veiculos_tracionadores",
                entidade_id=vehicle.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
