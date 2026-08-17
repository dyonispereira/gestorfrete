from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_document_dto import VehicleDocumentDTO
from modules.fleet.domain.entities.vehicle_document import VehicleDocument
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_document_repository import (
    SqlAlchemyVehicleDocumentRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateVehicleDocumentCommand(Command):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    tipo: str
    numero: str
    data_validade: date
    arquivo_id: uuid.UUID | None


class CreateVehicleDocumentHandler(CommandHandler[CreateVehicleDocumentCommand, VehicleDocumentDTO]):
    async def handle(self, command: CreateVehicleDocumentCommand) -> VehicleDocumentDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            if await vehicle_repo.get_by_id(command.vehicle_id) is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            document = VehicleDocument.create(
                veiculo_tracionador_id=command.vehicle_id,
                tipo=command.tipo,
                numero=command.numero,
                data_validade=command.data_validade,
                arquivo_id=command.arquivo_id,
            )
            doc_repo = SqlAlchemyVehicleDocumentRepository(uow.session)
            await doc_repo.add(document)
            await uow.commit()

        return VehicleDocumentDTO.from_entity(document)
