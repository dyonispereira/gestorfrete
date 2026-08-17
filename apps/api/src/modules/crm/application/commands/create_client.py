from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.crm.application.dtos.client_dto import ClientDTO
from modules.crm.domain.entities.client import Client
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateClientCommand(Command):
    actor: AuthenticatedActor
    razao_social: str
    nome_fantasia: str | None
    document: str
    telefone: str | None
    email: str | None


class CreateClientHandler(CommandHandler[CreateClientCommand, ClientDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateClientCommand) -> ClientDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyClientRepository(uow.session)

            if await repo.exists_with_document(command.document):
                raise ConflictError(
                    "CRM_CLIENT_DOCUMENT_ALREADY_EXISTS", "Já existe um Cliente com este CNPJ/CPF neste tenant."
                )

            now = datetime.now(timezone.utc)
            client = Client.create(
                codigo=str(uuid.uuid4())[:8],
                razao_social=command.razao_social,
                nome_fantasia=command.nome_fantasia,
                document=command.document,
                telefone=command.telefone,
                email=command.email,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(client)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="clientes",
                entidade_id=client.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"razao_social": client.razao_social, "document": client.document},
            )

            await uow.commit()

        return ClientDTO.from_entity(client)
