from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from modules.reporting.application.dtos.export_dto import ExportDTO
from modules.reporting.domain.entities.export import Export
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_export_repository import (
    SqlAlchemyExportRepository,
)
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateExportCommand(Command):
    actor: AuthenticatedActor
    saved_report_id: uuid.UUID | None
    filters: dict[str, Any] | None
    period: str | None


class CreateExportHandler(CommandHandler[CreateExportCommand, ExportDTO]):
    """`069` — D157: contexto sempre capturado pela aplicação no momento da chamada, nunca aceito
    como cópia literal do corpo. Se `saved_report_id` informado, resolve `metric_ids`/`filters`
    REAIS do Relatório Salvo agora (nunca o que o cliente enviou). D307 — nasce sempre
    `PROCESSANDO`, nunca `CONCLUIDA` na mesma transação."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateExportCommand) -> ExportDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            export_repo = SqlAlchemyExportRepository(uow.session)
            report_repo = SqlAlchemySavedReportRepository(uow.session)
            metric_repo = SqlAlchemyMetricRepository(uow.session)

            metric_ids: list[uuid.UUID]
            filters: dict[str, Any]
            if command.saved_report_id is not None:
                saved_report = await report_repo.get_by_id(command.saved_report_id)
                if saved_report is None:
                    raise NotFoundError("REPORTING_SAVED_REPORT_NOT_FOUND", "Relatório Salvo não encontrado.")
                metric_ids = saved_report.metricas_ids
                filters = saved_report.filtros or {}
            else:
                if not command.filters:
                    raise ValidationError(
                        "REPORTING_EXPORT_FILTERS_REQUIRED",
                        "Exportação avulsa (sem saved_report_id) exige filtros diretamente.",
                    )
                metric_ids = []
                filters = command.filters

            metric_versions: list[dict[str, Any]] = []
            for metric_id in metric_ids:
                metric = await metric_repo.get_by_id(metric_id)
                if metric is None:
                    raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica referenciada não encontrada.")
                metric_versions.append({"metric_id": str(metric.id), "version": metric.versao})

            now = datetime.now(timezone.utc)
            export = Export.request(
                relatorio_salvo_id=command.saved_report_id, usuario_id=command.actor.user_id,
                filtros_utilizados=filters, periodo=command.period or "", metricas_versoes=metric_versions,
                now=now,
            )
            await export_repo.add(export)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="exportacoes_geradas",
                entidade_id=export.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return ExportDTO.from_entity(export)
