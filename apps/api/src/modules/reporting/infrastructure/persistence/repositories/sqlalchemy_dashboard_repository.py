from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.reporting.domain.entities.dashboard import Dashboard
from modules.reporting.domain.repositories.dashboard_repository import DashboardRepository
from modules.reporting.domain.value_objects.dashboard_sharing import DashboardSharing
from modules.reporting.infrastructure.persistence.models.dashboard_model import DashboardModel


def _to_entity(model: DashboardModel) -> Dashboard:
    return Dashboard(
        id=model.id, usuario_id=model.usuario_id, nome=model.nome, layout=model.layout, widgets=model.widgets,
        filtros=model.filtros, permissoes_compartilhamento=DashboardSharing(model.permissoes_compartilhamento),
        preferencias=model.preferencias, status=model.status,
    )


class SqlAlchemyDashboardRepository(DashboardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Dashboard | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DashboardModel).where(DashboardModel.id == id, DashboardModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_name(self, usuario_id: uuid.UUID, nome: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(DashboardModel.id).where(
            DashboardModel.tenant_id == tenant_id, DashboardModel.usuario_id == usuario_id,
            DashboardModel.nome == nome,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_own_and_shared(
        self, *, page: int, limit: int, search: str | None, status: str | None, usuario_id: uuid.UUID,
        include_shared: bool,
    ) -> tuple[list[Dashboard], int]:
        tenant_id = get_current_tenant_id()
        own_clause = DashboardModel.usuario_id == usuario_id
        if include_shared:
            scope = or_(own_clause, DashboardModel.permissoes_compartilhamento != DashboardSharing.PRIVADO.value)
        else:
            scope = own_clause

        stmt = select(DashboardModel).where(DashboardModel.tenant_id == tenant_id, scope)
        if search is not None:
            stmt = stmt.where(DashboardModel.nome.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(DashboardModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(DashboardModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, dashboard: Dashboard) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(DashboardModel, dashboard.id)
        if model is None:
            model = DashboardModel(id=dashboard.id, tenant_id=tenant_id)
            self._session.add(model)
        model.usuario_id = dashboard.usuario_id
        model.nome = dashboard.nome
        model.layout = dashboard.layout
        model.widgets = dashboard.widgets
        model.filtros = dashboard.filtros
        model.permissoes_compartilhamento = dashboard.permissoes_compartilhamento.value
        model.preferencias = dashboard.preferencias
        model.status = dashboard.status
        await self._session.flush()
