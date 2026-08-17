from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.metric_dto import MetricDTO
from modules.analytics.domain.value_objects.metric_periodicity import MetricPeriodicity
from modules.analytics.domain.value_objects.metric_status import MetricStatus
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateMetricCommand(Command):
    actor: AuthenticatedActor
    metric_id: uuid.UUID
    name: str | None
    formula: str | None
    unit: str | None
    data_sources: dict[str, Any] | None
    calculation_periodicity: MetricPeriodicity | None
    status: MetricStatus | None


class UpdateMetricHandler(CommandHandler[UpdateMetricCommand, MetricDTO]):
    """`062` — mudar `formula` cria uma nova versão (D155/D419); os demais campos editam a mesma
    linha."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateMetricCommand) -> MetricDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyMetricRepository(uow.session)
            metric = await repo.get_by_id(command.metric_id)
            if metric is None:
                raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica não encontrada.")

            if command.formula is not None and command.formula != metric.formula:
                metric = metric.new_version(formula=command.formula)

            metric.update_fields(
                nome=command.name, unidade=command.unit, origem_dados=command.data_sources,
                periodicidade_calculo=command.calculation_periodicity, status=command.status,
            )
            await repo.add(metric)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="metricas", entidade_id=metric.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"version": metric.versao},
            )
            await uow.commit()

        return MetricDTO.from_entity(metric)
