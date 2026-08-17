from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.tracking.application.dtos.tracking_equipment_dto import TrackingEquipmentDTO
from modules.tracking.domain.value_objects.equipment_status import EquipmentStatus
from modules.tracking.domain.value_objects.equipment_type import EquipmentType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_equipment_repository import (
    SqlAlchemyTrackingEquipmentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateTrackingEquipmentCommand(Command):
    actor: AuthenticatedActor
    equipment_id: uuid.UUID
    vehicle_id: uuid.UUID | None
    ends_at: datetime | None
    status: EquipmentStatus | None


class UpdateTrackingEquipmentHandler(CommandHandler[UpdateTrackingEquipmentCommand, TrackingEquipmentDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateTrackingEquipmentCommand) -> TrackingEquipmentDTO:
        now = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTrackingEquipmentRepository(uow.session)
            equipment = await repo.get_by_id(command.equipment_id)
            if equipment is None:
                raise NotFoundError("TRACKING_EQUIPMENT_NOT_FOUND", "Equipamento de Rastreamento não encontrado.")

            target_vehicle_id = command.vehicle_id or equipment.veiculo_tracionador_id
            reassigning_to_principal = (
                command.vehicle_id is not None and equipment.tipo_equipamento == EquipmentType.PRINCIPAL
                and command.ends_at is None
            )
            if reassigning_to_principal and target_vehicle_id is not None:
                current_principal = await repo.get_principal_vigente(target_vehicle_id)
                if current_principal is not None and current_principal.id != equipment.id:
                    raise ConflictError(
                        "TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS",
                        "Este veículo já tem um equipamento PRINCIPAL vigente.",
                    )

            equipment.update(
                veiculo_tracionador_id=command.vehicle_id, ends_at=command.ends_at, status=command.status,
                alterado_por=command.actor.user_id, now=now,
            )
            await repo.add(equipment)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="equipamentos_rastreamento",
                entidade_id=equipment.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return TrackingEquipmentDTO.from_entity(equipment)
