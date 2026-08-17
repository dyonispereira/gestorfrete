from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_contact_dto import ClientContactDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_contact_repository import (
    SqlAlchemyClientContactRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateClientContactCommand(Command):
    actor: AuthenticatedActor
    client_id: uuid.UUID
    contact_id: uuid.UUID
    nome: str | None
    cargo: str | None
    telefone: str | None
    email: str | None


class UpdateClientContactHandler(CommandHandler[UpdateClientContactCommand, ClientContactDTO]):
    async def handle(self, command: UpdateClientContactCommand) -> ClientContactDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyClientContactRepository(uow.session)

            contact = await repo.get_by_id(command.contact_id)
            if contact is None or contact.cliente_id != command.client_id:
                raise NotFoundError("CRM_CLIENT_CONTACT_NOT_FOUND", "Contato não encontrado.")

            contact.update(
                nome=command.nome,
                cargo=command.cargo,
                telefone=command.telefone,
                email=command.email,
                now=datetime.now(timezone.utc),
            )
            await repo.add(contact)
            await uow.commit()

        return ClientContactDTO.from_entity(contact)
