from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.crm.application.dtos.client_dto import ClientDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateClientCommand(Command):
    actor: AuthenticatedActor
    client_id: uuid.UUID
    razao_social: str | None
    nome_fantasia: str | None
    telefone: str | None
    email: str | None


class UpdateClientHandler(CommandHandler[UpdateClientCommand, ClientDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateClientCommand) -> ClientDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyClientRepository(uow.session)

            client = await repo.get_by_id(command.client_id)
            if client is None:
                raise NotFoundError("CRM_CLIENT_NOT_FOUND", "Cliente não encontrado.")

            client.update(
                razao_social=command.razao_social,
                nome_fantasia=command.nome_fantasia,
                telefone=command.telefone,
                email=command.email,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(client)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="clientes",
                entidade_id=client.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return ClientDTO.from_entity(client)
