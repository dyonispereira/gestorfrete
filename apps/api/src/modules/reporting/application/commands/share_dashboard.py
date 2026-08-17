from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.dashboard_dto import DashboardDTO
from modules.reporting.domain.value_objects.dashboard_sharing import DashboardSharing
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_dashboard_repository import (
    SqlAlchemyDashboardRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ShareDashboardCommand(Command):
    actor: AuthenticatedActor
    dashboard_id: uuid.UUID
    sharing: DashboardSharing


class ShareDashboardHandler(CommandHandler[ShareDashboardCommand, DashboardDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ShareDashboardCommand) -> DashboardDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDashboardRepository(uow.session)
            dashboard = await repo.get_by_id(command.dashboard_id)
            if dashboard is None:
                raise NotFoundError("REPORTING_DASHBOARD_NOT_FOUND", "Dashboard não encontrado.")
            if dashboard.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_DASHBOARD_NOT_OWNED", "Só o dono compartilha o Dashboard.")

            dashboard.share(sharing=command.sharing)
            await repo.add(dashboard)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="dashboards_personalizados",
                entidade_id=dashboard.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"sharing": command.sharing.value},
            )
            await uow.commit()

        return DashboardDTO.from_entity(dashboard)
