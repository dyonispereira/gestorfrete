from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_cube_repository import (
    SqlAlchemyAnalyticsCubeRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from modules.reporting.application.dtos.scheduled_update_dto import ScheduledUpdateDTO
from modules.reporting.domain.entities.scheduled_update import ScheduledUpdate
from modules.reporting.domain.value_objects.scheduled_update_mode import ScheduledUpdateMode
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_scheduled_update_repository import (
    SqlAlchemyScheduledUpdateRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateScheduledUpdateCommand(Command):
    actor: AuthenticatedActor
    metric_id: uuid.UUID | None
    cube_id: uuid.UUID | None
    mode: ScheduledUpdateMode


class CreateScheduledUpdateHandler(CommandHandler[CreateScheduledUpdateCommand, ScheduledUpdateDTO]):
    """`070`/`ck_agendamentos_atualizacao_alvo` — exatamente um de `metric_id`/`cube_id`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateScheduledUpdateCommand) -> ScheduledUpdateDTO:
        if (command.metric_id is None) == (command.cube_id is None):
            raise ValidationError(
                "REPORTING_SCHEDULED_UPDATE_TARGET_REQUIRED", "Exatamente um de metric_id/cube_id é obrigatório."
            )

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyScheduledUpdateRepository(uow.session)

            if command.metric_id is not None:
                metric_repo = SqlAlchemyMetricRepository(uow.session)
                if await metric_repo.get_by_id(command.metric_id) is None:
                    raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica não encontrada.")
            if command.cube_id is not None:
                cube_repo = SqlAlchemyAnalyticsCubeRepository(uow.session)
                if await cube_repo.get_by_id(command.cube_id) is None:
                    raise NotFoundError("ANALYTICS_CUBE_NOT_FOUND", "Cubo Analítico não encontrado.")

            scheduled_update = ScheduledUpdate.create(
                tenant_id=command.actor.tenant_id, metrica_id=command.metric_id,
                cubo_analitico_id=command.cube_id, modo=command.mode,
            )
            await repo.add(scheduled_update)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="agendamentos_atualizacao",
                entidade_id=scheduled_update.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return ScheduledUpdateDTO.from_entity(scheduled_update)
