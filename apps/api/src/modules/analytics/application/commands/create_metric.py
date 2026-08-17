from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.analytics.application.dtos.metric_dto import MetricDTO
from modules.analytics.domain.entities.metric import Metric
from modules.analytics.domain.value_objects.metric_dimensional_granularity import MetricDimensionalGranularity
from modules.analytics.domain.value_objects.metric_periodicity import MetricPeriodicity
from modules.analytics.domain.value_objects.metric_temporal_granularity import MetricTemporalGranularity
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateMetricCommand(Command):
    actor: AuthenticatedActor
    name: str
    formula: str
    temporal_granularity: MetricTemporalGranularity
    dimensional_granularity: MetricDimensionalGranularity
    unit: str
    data_sources: dict[str, Any] | None
    calculation_periodicity: MetricPeriodicity


class CreateMetricHandler(CommandHandler[CreateMetricCommand, MetricDTO]):
    """D419 — `version` sempre nasce `1`, nunca aceito no corpo. Unicidade de `name` checada contra
    a versão mais recente de qualquer linhagem existente no tenant (nunca uma constraint física —
    `metricas` não tem `UNIQUE(tenant_id, nome)` de propósito)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateMetricCommand) -> MetricDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyMetricRepository(uow.session)

            if await repo.get_latest_by_name(command.name, tenant_id=command.actor.tenant_id) is not None:
                raise ConflictError("ANALYTICS_METRIC_NAME_ALREADY_EXISTS", "Já existe uma Métrica com esse nome.")

            metric = Metric.create(
                tenant_id=command.actor.tenant_id, nome=command.name, formula=command.formula,
                granularidade_temporal=command.temporal_granularity,
                granularidade_dimensional=command.dimensional_granularity, unidade=command.unit,
                origem_dados=command.data_sources or {}, periodicidade_calculo=command.calculation_periodicity,
            )
            await repo.add(metric)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="metricas", entidade_id=metric.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"name": command.name, "version": 1},
            )
            await uow.commit()

        return MetricDTO.from_entity(metric)
