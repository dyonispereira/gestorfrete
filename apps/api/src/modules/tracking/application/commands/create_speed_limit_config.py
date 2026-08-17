from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from modules.tracking.application.dtos.speed_limit_config_dto import SpeedLimitConfigDTO
from modules.tracking.domain.entities.speed_limit_config import SpeedLimitConfig
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_speed_limit_config_repository import (
    SqlAlchemySpeedLimitConfigRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateSpeedLimitConfigCommand(Command):
    actor: AuthenticatedActor
    vehicle_category_id: uuid.UUID | None
    limit_kmh: float


class CreateSpeedLimitConfigHandler(CommandHandler[CreateSpeedLimitConfigCommand, SpeedLimitConfigDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateSpeedLimitConfigCommand) -> SpeedLimitConfigDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySpeedLimitConfigRepository(uow.session)
            category_repo = SqlAlchemyVehicleCategoryRepository(uow.session)

            if command.vehicle_category_id is not None:
                if await category_repo.get_by_id(command.vehicle_category_id) is None:
                    raise NotFoundError("TRACKING_SPEED_LIMIT_CONFIG_CATEGORY_NOT_FOUND", "Categoria de Veículo não encontrada.")

            config = SpeedLimitConfig.create(
                categoria_veiculo_id=command.vehicle_category_id, limite_kmh=command.limit_kmh
            )
            await repo.add(config)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_limite_velocidade",
                entidade_id=config.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"limite_kmh": str(config.limite_kmh)},
            )
            await uow.commit()

        return SpeedLimitConfigDTO.from_entity(config)
