from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.dashboard_dto import DashboardDTO
from modules.reporting.domain.value_objects.dashboard_sharing import DashboardSharing
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_dashboard_repository import (
    SqlAlchemyDashboardRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetDashboardQuery(Query):
    actor: AuthenticatedActor
    dashboard_id: uuid.UUID
    has_view_shared_permission: bool


class GetDashboardHandler(QueryHandler[GetDashboardQuery, DashboardDTO]):
    """`066` — `.view_own` (dono) ou `.view_shared` (`sharing != PRIVADO`) — `403` caso contrário."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetDashboardQuery) -> DashboardDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDashboardRepository(session)
            dashboard = await repo.get_by_id(query.dashboard_id)
        if dashboard is None:
            raise NotFoundError("REPORTING_DASHBOARD_NOT_FOUND", "Dashboard não encontrado.")

        is_owner = dashboard.usuario_id == query.actor.user_id
        is_shared_visible = (
            query.has_view_shared_permission and dashboard.permissoes_compartilhamento != DashboardSharing.PRIVADO
        )
        if not is_owner and not is_shared_visible:
            raise AuthorizationError("REPORTING_DASHBOARD_FORBIDDEN", "Dashboard não pertence nem foi compartilhado com o usuário.")

        return DashboardDTO.from_entity(dashboard)
