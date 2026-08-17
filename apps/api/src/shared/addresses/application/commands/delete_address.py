from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SqlAlchemyAddressRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteAddressCommand(Command):
    actor: AuthenticatedActor
    owner_type: OwnerType
    owner_id: uuid.UUID
    address_id: uuid.UUID


class DeleteAddressHandler(CommandHandler[DeleteAddressCommand, None]):
    async def handle(self, command: DeleteAddressCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAddressRepository(uow.session)

            address = await repo.get_by_id(command.address_id)
            if address is None or address.owner_type != command.owner_type or address.owner_id != command.owner_id:
                raise NotFoundError("ADDRESS_NOT_FOUND", "Endereço não encontrado.")

            address.soft_delete(deleted_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(address)
            await uow.commit()
