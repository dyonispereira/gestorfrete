from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.saved_report_dto import SavedReportDTO
from modules.reporting.domain.value_objects.output_format import OutputFormat
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateSavedReportCommand(Command):
    actor: AuthenticatedActor
    saved_report_id: uuid.UUID
    name: str | None
    metric_ids: list[uuid.UUID] | None
    filters: dict[str, Any] | None
    output_format: OutputFormat | None
    status: str | None


class UpdateSavedReportHandler(CommandHandler[UpdateSavedReportCommand, SavedReportDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateSavedReportCommand) -> SavedReportDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySavedReportRepository(uow.session)
            saved_report = await repo.get_by_id(command.saved_report_id)
            if saved_report is None:
                raise NotFoundError("REPORTING_SAVED_REPORT_NOT_FOUND", "Relatório Salvo não encontrado.")
            if saved_report.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_SAVED_REPORT_NOT_OWNED", "Só o dono edita o Relatório Salvo.")

            saved_report.update(
                nome=command.name, metricas_ids=command.metric_ids, filtros=command.filters,
                formato_saida=command.output_format, status=command.status,
            )
            await repo.add(saved_report)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="relatorios_salvos",
                entidade_id=saved_report.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return SavedReportDTO.from_entity(saved_report)
