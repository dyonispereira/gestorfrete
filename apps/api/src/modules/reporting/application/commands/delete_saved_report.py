from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteSavedReportCommand(Command):
    actor: AuthenticatedActor
    saved_report_id: uuid.UUID


class DeleteSavedReportHandler(CommandHandler[DeleteSavedReportCommand, None]):
    """`068` — excluir um Relatório Salvo referenciado por uma Export não apaga a Exportação já
    gerada (D001, histórico nunca quebra por desativação de cadastro)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteSavedReportCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySavedReportRepository(uow.session)
            saved_report = await repo.get_by_id(command.saved_report_id)
            if saved_report is None:
                raise NotFoundError("REPORTING_SAVED_REPORT_NOT_FOUND", "Relatório Salvo não encontrado.")
            if saved_report.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_SAVED_REPORT_NOT_OWNED", "Só o dono exclui o Relatório Salvo.")

            saved_report.archive()
            await repo.add(saved_report)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="relatorios_salvos",
                entidade_id=saved_report.id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
