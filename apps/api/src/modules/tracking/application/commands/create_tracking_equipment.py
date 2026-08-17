from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.tracking.application.dtos.tracking_equipment_dto import TrackingEquipmentDTO
from modules.tracking.domain.entities.tracking_equipment import TrackingEquipment
from modules.tracking.domain.value_objects.equipment_type import EquipmentType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_equipment_repository import (
    SqlAlchemyTrackingEquipmentRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_provider_repository import (
    SqlAlchemyTrackingProviderRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateTrackingEquipmentCommand(Command):
    actor: AuthenticatedActor
    provider_id: uuid.UUID
    serial_identifier: str
    equipment_type: EquipmentType
    vehicle_id: uuid.UUID | None


class CreateTrackingEquipmentHandler(CommandHandler[CreateTrackingEquipmentCommand, TrackingEquipmentDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateTrackingEquipmentCommand) -> TrackingEquipmentDTO:
        now = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            provider_repo = SqlAlchemyTrackingProviderRepository(uow.session)
            equipment_repo = SqlAlchemyTrackingEquipmentRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)

            if await provider_repo.get_by_id(command.provider_id) is None:
                raise NotFoundError("TRACKING_EQUIPMENT_PROVIDER_NOT_FOUND", "Provedor de Rastreamento não encontrado.")
            if await equipment_repo.get_by_serial(command.serial_identifier) is not None:
                raise ConflictError(
                    "TRACKING_EQUIPMENT_SERIAL_ALREADY_EXISTS", "Identificador serial já cadastrado."
                )
            if command.vehicle_id is not None:
                if await vehicle_repo.get_by_id(command.vehicle_id) is None:
                    raise NotFoundError("TRACKING_EQUIPMENT_VEHICLE_NOT_FOUND", "Veículo não encontrado.")
                if (
                    command.equipment_type == EquipmentType.PRINCIPAL
                    and await equipment_repo.get_principal_vigente(command.vehicle_id) is not None
                ):
                    raise ConflictError(
                        "TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS",
                        "Este veículo já tem um equipamento PRINCIPAL vigente — encerre a vigência atual antes de criar um novo.",
                    )

            equipment = TrackingEquipment.create(
                provedor_rastreamento_id=command.provider_id, identificador_serial=command.serial_identifier,
                tipo_equipamento=command.equipment_type, veiculo_tracionador_id=command.vehicle_id, now=now,
            )
            await equipment_repo.add(equipment)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="equipamentos_rastreamento",
                entidade_id=equipment.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"identificador_serial": equipment.identificador_serial},
            )
            await uow.commit()

        return TrackingEquipmentDTO.from_entity(equipment)
