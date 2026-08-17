from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_document_repository import (
    SqlAlchemyDriverDocumentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteDriverDocumentCommand(Command):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    document_id: uuid.UUID


class DeleteDriverDocumentHandler(CommandHandler[DeleteDriverDocumentCommand, None]):
    async def handle(self, command: DeleteDriverDocumentCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDriverDocumentRepository(uow.session)

            document = await repo.get_by_id(command.document_id)
            if document is None or document.motorista_id != command.driver_id:
                raise NotFoundError("DRIVERS_DOCUMENT_NOT_FOUND", "Documento não encontrado.")

            await repo.delete(document)
            await uow.commit()
