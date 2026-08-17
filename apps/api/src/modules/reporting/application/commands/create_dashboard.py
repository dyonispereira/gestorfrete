from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_consolidated_indicator_repository import (
    SqlAlchemyConsolidatedIndicatorRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from modules.reporting.application.dtos.dashboard_dto import DashboardDTO
from modules.reporting.domain.entities.dashboard import Dashboard
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_dashboard_repository import (
    SqlAlchemyDashboardRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateDashboardCommand(Command):
    actor: AuthenticatedActor
    name: str
    layout: dict[str, Any]
    widgets: list[dict[str, Any]]
    filters: dict[str, Any] | None
    preferences: dict[str, Any] | None


class CreateDashboardHandler(CommandHandler[CreateDashboardCommand, DashboardDTO]):
    """`066` — cada widget referencia `metric_id` **ou** `indicator_id` (D158), nunca copia valor;
    ambos validados contra `analytics` se informados."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateDashboardCommand) -> DashboardDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            dashboard_repo = SqlAlchemyDashboardRepository(uow.session)
            metric_repo = SqlAlchemyMetricRepository(uow.session)
            indicator_repo = SqlAlchemyConsolidatedIndicatorRepository(uow.session)

            if await dashboard_repo.exists_with_name(command.actor.user_id, command.name):
                raise ConflictError("REPORTING_DASHBOARD_NAME_ALREADY_EXISTS", "Já existe um Dashboard com esse nome.")

            for widget in command.widgets:
                metric_id = widget.get("metric_id")
                indicator_id = widget.get("indicator_id")
                if metric_id is not None and await metric_repo.get_by_id(uuid.UUID(str(metric_id))) is None:
                    raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica referenciada não encontrada.")
                if indicator_id is not None and await indicator_repo.get_by_id(uuid.UUID(str(indicator_id))) is None:
                    raise NotFoundError("ANALYTICS_INDICATOR_NOT_FOUND", "Indicador referenciado não encontrado.")

            dashboard = Dashboard.create(
                usuario_id=command.actor.user_id, nome=command.name, layout=command.layout,
                widgets=command.widgets, filtros=command.filters, preferencias=command.preferences,
            )
            await dashboard_repo.add(dashboard)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="dashboards_personalizados",
                entidade_id=dashboard.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"name": command.name},
            )
            await uow.commit()

        return DashboardDTO.from_entity(dashboard)
