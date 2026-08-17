from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_document_dto import DriverDocumentDTO
from modules.drivers.domain.entities.driver_document import DriverDocument
from modules.drivers.domain.value_objects.cnh_category import CnhCategory
from modules.drivers.domain.value_objects.document_type import DocumentType
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_document_repository import (
    SqlAlchemyDriverDocumentRepository,
)
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateDriverDocumentCommand(Command):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    tipo_documento: DocumentType
    numero: str
    categoria_cnh: CnhCategory | None
    data_validade: date | None
    arquivo_id: uuid.UUID | None


class CreateDriverDocumentHandler(CommandHandler[CreateDriverDocumentCommand, DriverDocumentDTO]):
    async def handle(self, command: CreateDriverDocumentCommand) -> DriverDocumentDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            if await driver_repo.get_by_id(command.driver_id) is None:
                raise NotFoundError("DRIVERS_DRIVER_NOT_FOUND", "Motorista não encontrado.")

            document = DriverDocument.create(
                motorista_id=command.driver_id,
                tipo_documento=command.tipo_documento,
                numero=command.numero,
                categoria_cnh=command.categoria_cnh,
                data_validade=command.data_validade,
                arquivo_id=command.arquivo_id,
                now=datetime.now(timezone.utc),
            )
            doc_repo = SqlAlchemyDriverDocumentRepository(uow.session)
            await doc_repo.add(document)
            await uow.commit()

        return DriverDocumentDTO.from_entity(document)
