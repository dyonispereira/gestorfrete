from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from shared.addresses.application.dtos.address_dto import AddressDTO
from shared.addresses.domain.entities.address import Address
from shared.addresses.domain.value_objects.address_type import AddressType
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SqlAlchemyAddressRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateAddressCommand(Command):
    actor: AuthenticatedActor
    owner_type: OwnerType
    owner_id: uuid.UUID
    tipo: AddressType
    logradouro: str
    numero: str | None
    complemento: str | None
    bairro: str
    cidade: str
    uf: str
    cep: str


class CreateAddressHandler(CommandHandler[CreateAddressCommand, AddressDTO]):
    """Chamado pelo router do dono (`crm`/`maintenance`) **depois** de confirmar que o dono existe
    (`404` antes de chegar aqui) — nunca valida isso sozinho, não sabe como (D354)."""

    async def handle(self, command: CreateAddressCommand) -> AddressDTO:
        # `has_principal` + `INSERT` seria um check-then-act com janela de corrida real entre duas
        # requisições concorrentes — a única fonte de verdade é o índice único parcial físico
        # (`uq_enderecos_entidade_principal`), nunca uma checagem prévia em Application
        # (`ADDRESS_IMPLEMENTATION.md`).
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAddressRepository(uow.session)

            now = datetime.now(timezone.utc)
            address = Address.create(
                owner_type=command.owner_type,
                owner_id=command.owner_id,
                tipo=command.tipo,
                logradouro=command.logradouro,
                numero=command.numero,
                complemento=command.complemento,
                bairro=command.bairro,
                cidade=command.cidade,
                uf=command.uf,
                cep=command.cep,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            try:
                # `repo.add()` chama `session.flush()` internamente — é aí que o índice único
                # parcial dispara `IntegrityError`, não em `uow.commit()`; o `try` precisa envolver
                # os dois, senão a exceção escapa antes de chegar ao `except` (achado real de
                # execução, não uma suposição — Sprint 11 Lote 3).
                await repo.add(address)
                await uow.commit()
            except IntegrityError as exc:
                await uow.rollback()
                raise ConflictError(
                    "ADDRESS_PRINCIPAL_ALREADY_EXISTS",
                    "Já existe um endereço Principal vigente para este dono.",
                ) from exc

        return AddressDTO.from_entity(address)
