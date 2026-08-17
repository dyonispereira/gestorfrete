from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_document_dto import VehicleDocumentDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_document_repository import (
    SqlAlchemyVehicleDocumentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateVehicleDocumentCommand(Command):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    document_id: uuid.UUID
    numero: str | None
    data_validade: date | None
    arquivo_id: uuid.UUID | None


class UpdateVehicleDocumentHandler(CommandHandler[UpdateVehicleDocumentCommand, VehicleDocumentDTO]):
    async def handle(self, command: UpdateVehicleDocumentCommand) -> VehicleDocumentDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleDocumentRepository(uow.session)

            document = await repo.get_by_id(command.document_id)
            if document is None or document.veiculo_tracionador_id != command.vehicle_id:
                raise NotFoundError("FLEET_VEHICLE_DOCUMENT_NOT_FOUND", "Documento não encontrado.")

            document.update(numero=command.numero, data_validade=command.data_validade, arquivo_id=command.arquivo_id)
            await repo.add(document)
            await uow.commit()

        return VehicleDocumentDTO.from_entity(document)
