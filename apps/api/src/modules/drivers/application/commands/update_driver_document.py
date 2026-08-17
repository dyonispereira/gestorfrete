from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_document_dto import DriverDocumentDTO
from modules.drivers.domain.value_objects.cnh_category import CnhCategory
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_document_repository import (
    SqlAlchemyDriverDocumentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateDriverDocumentCommand(Command):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    document_id: uuid.UUID
    numero: str | None
    categoria_cnh: CnhCategory | None
    data_validade: date | None
    arquivo_id: uuid.UUID | None


class UpdateDriverDocumentHandler(CommandHandler[UpdateDriverDocumentCommand, DriverDocumentDTO]):
    async def handle(self, command: UpdateDriverDocumentCommand) -> DriverDocumentDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDriverDocumentRepository(uow.session)

            document = await repo.get_by_id(command.document_id)
            if document is None or document.motorista_id != command.driver_id:
                raise NotFoundError("DRIVERS_DOCUMENT_NOT_FOUND", "Documento não encontrado.")

            document.update(
                numero=command.numero,
                categoria_cnh=command.categoria_cnh,
                data_validade=command.data_validade,
                arquivo_id=command.arquivo_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(document)
            await uow.commit()

        return DriverDocumentDTO.from_entity(document)
