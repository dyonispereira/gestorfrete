from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.analytics_cube_dto import AnalyticsCubeDTO
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_cube_repository import (
    SqlAlchemyAnalyticsCubeRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAnalyticsCubeCommand(Command):
    actor: AuthenticatedActor
    cube_id: uuid.UUID
    dimensions: list[str] | None
    metric_ids: list[uuid.UUID] | None
    status: str | None


class UpdateAnalyticsCubeHandler(CommandHandler[UpdateAnalyticsCubeCommand, AnalyticsCubeDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateAnalyticsCubeCommand) -> AnalyticsCubeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            cube_repo = SqlAlchemyAnalyticsCubeRepository(uow.session)
            metric_repo = SqlAlchemyMetricRepository(uow.session)

            cube = await cube_repo.get_by_id(command.cube_id)
            if cube is None:
                raise NotFoundError("ANALYTICS_CUBE_NOT_FOUND", "Cubo Analítico não encontrado.")

            if command.metric_ids is not None:
                for metric_id in command.metric_ids:
                    if await metric_repo.get_by_id(metric_id) is None:
                        raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica referenciada não encontrada.")

            cube.update(dimensoes=command.dimensions, metricas_ids=command.metric_ids, status=command.status)
            await cube_repo.add(cube)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cubos_analiticos",
                entidade_id=cube.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return AnalyticsCubeDTO.from_entity(cube)
