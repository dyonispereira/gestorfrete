from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_dashboard_repository import (
    SqlAlchemyDashboardRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteDashboardCommand(Command):
    actor: AuthenticatedActor
    dashboard_id: uuid.UUID


class DeleteDashboardHandler(CommandHandler[DeleteDashboardCommand, None]):
    """D219/D422 — soft delete via `status=ARQUIVADO` (sem `excluido_em` na DDL congelada)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteDashboardCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDashboardRepository(uow.session)
            dashboard = await repo.get_by_id(command.dashboard_id)
            if dashboard is None:
                raise NotFoundError("REPORTING_DASHBOARD_NOT_FOUND", "Dashboard não encontrado.")
            if dashboard.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_DASHBOARD_NOT_OWNED", "Só o dono exclui o Dashboard.")

            dashboard.archive()
            await repo.add(dashboard)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="dashboards_personalizados",
                entidade_id=dashboard.id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
