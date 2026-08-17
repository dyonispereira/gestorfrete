from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.speed_limit_config_dto import SpeedLimitConfigDTO
from modules.tracking.domain.value_objects.speed_limit_config_status import SpeedLimitConfigStatus
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_speed_limit_config_repository import (
    SqlAlchemySpeedLimitConfigRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateSpeedLimitConfigCommand(Command):
    actor: AuthenticatedActor
    speed_limit_config_id: uuid.UUID
    limit_kmh: float | None
    status: SpeedLimitConfigStatus | None


class UpdateSpeedLimitConfigHandler(CommandHandler[UpdateSpeedLimitConfigCommand, SpeedLimitConfigDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateSpeedLimitConfigCommand) -> SpeedLimitConfigDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySpeedLimitConfigRepository(uow.session)
            config = await repo.get_by_id(command.speed_limit_config_id)
            if config is None:
                raise NotFoundError("TRACKING_SPEED_LIMIT_CONFIG_NOT_FOUND", "Configuração de Limite de Velocidade não encontrada.")

            config.update(limite_kmh=command.limit_kmh, status=command.status)
            await repo.add(config)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_limite_velocidade",
                entidade_id=config.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return SpeedLimitConfigDTO.from_entity(config)
