from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.analytics.application.dtos.analytics_cube_dto import AnalyticsCubeDTO
from modules.analytics.domain.entities.analytics_cube import AnalyticsCube
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_cube_repository import (
    SqlAlchemyAnalyticsCubeRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateAnalyticsCubeCommand(Command):
    actor: AuthenticatedActor
    name: str
    dimensions: list[str]
    metric_ids: list[uuid.UUID]


class CreateAnalyticsCubeHandler(CommandHandler[CreateAnalyticsCubeCommand, AnalyticsCubeDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateAnalyticsCubeCommand) -> AnalyticsCubeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            cube_repo = SqlAlchemyAnalyticsCubeRepository(uow.session)
            metric_repo = SqlAlchemyMetricRepository(uow.session)

            if await cube_repo.exists_with_name(command.actor.tenant_id, command.name):
                raise ConflictError("ANALYTICS_CUBE_NAME_ALREADY_EXISTS", "Já existe um Cubo com esse nome.")
            for metric_id in command.metric_ids:
                if await metric_repo.get_by_id(metric_id) is None:
                    raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica referenciada não encontrada.")

            cube = AnalyticsCube.create(
                tenant_id=command.actor.tenant_id, nome=command.name, dimensoes=command.dimensions,
                metricas_ids=command.metric_ids,
            )
            await cube_repo.add(cube)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cubos_analiticos",
                entidade_id=cube.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"name": command.name},
            )
            await uow.commit()

        return AnalyticsCubeDTO.from_entity(cube)
