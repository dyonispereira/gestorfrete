from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_contact_dto import ClientContactDTO
from modules.crm.domain.entities.client_contact import ClientContact
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_contact_repository import (
    SqlAlchemyClientContactRepository,
)
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateClientContactCommand(Command):
    actor: AuthenticatedActor
    client_id: uuid.UUID
    nome: str
    cargo: str | None
    telefone: str | None
    email: str | None


class CreateClientContactHandler(CommandHandler[CreateClientContactCommand, ClientContactDTO]):
    async def handle(self, command: CreateClientContactCommand) -> ClientContactDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            client_repo = SqlAlchemyClientRepository(uow.session)
            contact_repo = SqlAlchemyClientContactRepository(uow.session)

            if await client_repo.get_by_id(command.client_id) is None:
                raise NotFoundError("CRM_CLIENT_NOT_FOUND", "Cliente não encontrado.")

            contact = ClientContact.create(
                cliente_id=command.client_id,
                nome=command.nome,
                cargo=command.cargo,
                telefone=command.telefone,
                email=command.email,
                now=datetime.now(timezone.utc),
            )
            await contact_repo.add(contact)
            await uow.commit()

        return ClientContactDTO.from_entity(contact)
