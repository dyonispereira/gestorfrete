from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.reporting.domain.entities.export import Export
from modules.reporting.domain.repositories.export_repository import ExportRepository
from modules.reporting.domain.value_objects.export_status import ExportStatus
from modules.reporting.infrastructure.persistence.models.export_model import ExportModel


def _to_entity(model: ExportModel) -> Export:
    return Export(
        id=model.id, relatorio_salvo_id=model.relatorio_salvo_id, usuario_id=model.usuario_id,
        filtros_utilizados=model.filtros_utilizados, periodo=model.periodo,
        metricas_versoes=model.metricas_versoes, arquivo_id=model.arquivo_id,
        mensagem_erro=model.mensagem_erro, data_hora_solicitacao=model.data_hora_solicitacao,
        status=ExportStatus(model.status),
    )


class SqlAlchemyExportRepository(ExportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Export | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ExportModel).where(ExportModel.id == id, ExportModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, status: str | None, saved_report_id: uuid.UUID | None, usuario_id: uuid.UUID
    ) -> tuple[list[Export], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ExportModel).where(ExportModel.tenant_id == tenant_id, ExportModel.usuario_id == usuario_id)
        if status is not None:
            stmt = stmt.where(ExportModel.status == status)
        if saved_report_id is not None:
            stmt = stmt.where(ExportModel.relatorio_salvo_id == saved_report_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ExportModel.data_hora_solicitacao.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, export: Export) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ExportModel, export.id)
        if model is None:
            model = ExportModel(id=export.id, tenant_id=tenant_id)
            self._session.add(model)
        model.relatorio_salvo_id = export.relatorio_salvo_id
        model.usuario_id = export.usuario_id
        model.filtros_utilizados = export.filtros_utilizados
        model.periodo = export.periodo
        model.metricas_versoes = export.metricas_versoes
        model.arquivo_id = export.arquivo_id
        model.mensagem_erro = export.mensagem_erro
        model.data_hora_solicitacao = export.data_hora_solicitacao
        model.status = export.status.value
        await self._session.flush()
