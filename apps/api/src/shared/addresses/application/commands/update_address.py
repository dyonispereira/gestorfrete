from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from shared.addresses.application.dtos.address_dto import AddressDTO
from shared.addresses.domain.value_objects.address_type import AddressType
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SqlAlchemyAddressRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAddressCommand(Command):
    actor: AuthenticatedActor
    owner_type: OwnerType
    owner_id: uuid.UUID
    address_id: uuid.UUID
    tipo: AddressType | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    cep: str | None


class UpdateAddressHandler(CommandHandler[UpdateAddressCommand, AddressDTO]):
    async def handle(self, command: UpdateAddressCommand) -> AddressDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAddressRepository(uow.session)

            address = await repo.get_by_id(command.address_id)
            if address is None or address.owner_type != command.owner_type or address.owner_id != command.owner_id:
                raise NotFoundError("ADDRESS_NOT_FOUND", "Endereço não encontrado.")

            address.update(
                tipo=command.tipo,
                logradouro=command.logradouro,
                numero=command.numero,
                complemento=command.complemento,
                bairro=command.bairro,
                cidade=command.cidade,
                uf=command.uf,
                cep=command.cep,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            try:
                # `repo.add()` chama `session.flush()` internamente — ver nota em
                # `create_address.py` (mesmo achado real).
                await repo.add(address)
                await uow.commit()
            except IntegrityError as exc:
                await uow.rollback()
                raise ConflictError(
                    "ADDRESS_PRINCIPAL_ALREADY_EXISTS",
                    "Já existe um endereço Principal vigente para este dono.",
                ) from exc

        return AddressDTO.from_entity(address)
