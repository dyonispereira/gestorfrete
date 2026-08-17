from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.integration_config_dto import IntegrationConfigDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_integration_config_repository import (
    SqlAlchemyIntegrationConfigRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class EnableIntegrationConfigCommand(Command):
    actor: AuthenticatedActor
    config_id: uuid.UUID


@dataclass(frozen=True)
class DisableIntegrationConfigCommand(Command):
    actor: AuthenticatedActor
    config_id: uuid.UUID


class EnableIntegrationConfigHandler(CommandHandler[EnableIntegrationConfigCommand, IntegrationConfigDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: EnableIntegrationConfigCommand) -> IntegrationConfigDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyIntegrationConfigRepository(uow.session)
            config = await repo.get_by_id(command.config_id)
            if config is None:
                raise NotFoundError("INTEGRATION_CONFIG_NOT_FOUND", "Configuração de Integração não encontrada.")
            config.enable()
            await repo.add(config)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_integracao",
                entidade_id=config.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": "ATIVA"},
            )
            await uow.commit()
        return IntegrationConfigDTO.from_entity(config)


class DisableIntegrationConfigHandler(CommandHandler[DisableIntegrationConfigCommand, IntegrationConfigDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DisableIntegrationConfigCommand) -> IntegrationConfigDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyIntegrationConfigRepository(uow.session)
            config = await repo.get_by_id(command.config_id)
            if config is None:
                raise NotFoundError("INTEGRATION_CONFIG_NOT_FOUND", "Configuração de Integração não encontrada.")
            config.disable()
            await repo.add(config)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_integracao",
                entidade_id=config.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": "INATIVA"},
            )
            await uow.commit()
        return IntegrationConfigDTO.from_entity(config)
