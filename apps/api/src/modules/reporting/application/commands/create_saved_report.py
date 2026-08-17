from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from modules.reporting.application.dtos.saved_report_dto import SavedReportDTO
from modules.reporting.domain.entities.saved_report import SavedReport
from modules.reporting.domain.value_objects.output_format import OutputFormat
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateSavedReportCommand(Command):
    actor: AuthenticatedActor
    name: str
    metric_ids: list[uuid.UUID]
    filters: dict[str, Any] | None
    output_format: OutputFormat


class CreateSavedReportHandler(CommandHandler[CreateSavedReportCommand, SavedReportDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateSavedReportCommand) -> SavedReportDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            report_repo = SqlAlchemySavedReportRepository(uow.session)
            metric_repo = SqlAlchemyMetricRepository(uow.session)

            if await report_repo.exists_with_name(command.actor.user_id, command.name):
                raise ConflictError("REPORTING_SAVED_REPORT_NAME_ALREADY_EXISTS", "Já existe um Relatório com esse nome.")
            for metric_id in command.metric_ids:
                if await metric_repo.get_by_id(metric_id) is None:
                    raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica referenciada não encontrada.")

            saved_report = SavedReport.create(
                usuario_id=command.actor.user_id, nome=command.name, metricas_ids=command.metric_ids,
                filtros=command.filters, formato_saida=command.output_format,
            )
            await report_repo.add(saved_report)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="relatorios_salvos",
                entidade_id=saved_report.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"name": command.name},
            )
            await uow.commit()

        return SavedReportDTO.from_entity(saved_report)
