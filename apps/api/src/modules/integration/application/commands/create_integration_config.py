from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.session import get_session_factory
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.integration_config_dto import IntegrationConfigDTO
from modules.integration.domain.entities.integration_config import IntegrationConfig
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_integration_config_repository import (
    SqlAlchemyIntegrationConfigRepository,
)
from modules.storage.application.queries.get_file import GetFileHandler, GetFileQuery
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateIntegrationConfigCommand(Command):
    actor: AuthenticatedActor
    type: str
    credential_file_id: uuid.UUID


class CreateIntegrationConfigHandler(CommandHandler[CreateIntegrationConfigCommand, IntegrationConfigDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateIntegrationConfigCommand) -> IntegrationConfigDTO:
        file_dto = await GetFileHandler(get_session_factory()).handle(
            GetFileQuery(actor=command.actor, file_id=command.credential_file_id)
        )
        if file_dto.status != "ATIVO":
            raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo de credencial não encontrado.")

        config = IntegrationConfig.create(tipo=command.type, credencial_arquivo_id=command.credential_file_id)

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyIntegrationConfigRepository(uow.session)
            await repo.add(config)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_integracao",
                entidade_id=config.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"type": command.type},
            )
            await uow.commit()

        return IntegrationConfigDTO.from_entity(config)
