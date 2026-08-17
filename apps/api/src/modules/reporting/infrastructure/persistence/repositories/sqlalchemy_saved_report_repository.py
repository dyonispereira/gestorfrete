from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.reporting.domain.entities.saved_report import SavedReport
from modules.reporting.domain.repositories.saved_report_repository import SavedReportRepository
from modules.reporting.domain.value_objects.output_format import OutputFormat
from modules.reporting.infrastructure.persistence.models.saved_report_model import (
    SavedReportMetricModel,
    SavedReportModel,
)


class SqlAlchemySavedReportRepository(SavedReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _to_entity(self, model: SavedReportModel) -> SavedReport:
        metric_ids_stmt = select(SavedReportMetricModel.metrica_id).where(
            SavedReportMetricModel.relatorio_salvo_id == model.id
        )
        metric_ids = list((await self._session.execute(metric_ids_stmt)).scalars().all())
        return SavedReport(
            id=model.id, usuario_id=model.usuario_id, nome=model.nome, metricas_ids=metric_ids,
            filtros=model.filtros, formato_saida=OutputFormat(model.formato_saida), status=model.status,
        )

    async def get_by_id(self, id: uuid.UUID) -> SavedReport | None:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedReportModel).where(SavedReportModel.id == id, SavedReportModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return await self._to_entity(model) if model is not None else None

    async def exists_with_name(self, usuario_id: uuid.UUID, nome: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedReportModel.id).where(
            SavedReportModel.tenant_id == tenant_id, SavedReportModel.usuario_id == usuario_id,
            SavedReportModel.nome == nome,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, output_format: str | None, status: str | None,
        usuario_id: uuid.UUID,
    ) -> tuple[list[SavedReport], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(SavedReportModel).where(
            SavedReportModel.tenant_id == tenant_id, SavedReportModel.usuario_id == usuario_id
        )
        if search is not None:
            stmt = stmt.where(SavedReportModel.nome.ilike(f"%{search}%"))
        if output_format is not None:
            stmt = stmt.where(SavedReportModel.formato_saida == output_format)
        if status is not None:
            stmt = stmt.where(SavedReportModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SavedReportModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [await self._to_entity(m) for m in models], total

    async def add(self, saved_report: SavedReport) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(SavedReportModel, saved_report.id)
        if model is None:
            model = SavedReportModel(id=saved_report.id, tenant_id=tenant_id)
            self._session.add(model)
        model.usuario_id = saved_report.usuario_id
        model.nome = saved_report.nome
        model.filtros = saved_report.filtros
        model.formato_saida = saved_report.formato_saida.value
        model.status = saved_report.status
        await self._session.flush()

        await self._session.execute(
            delete(SavedReportMetricModel).where(SavedReportMetricModel.relatorio_salvo_id == saved_report.id)
        )
        if saved_report.metricas_ids:
            stmt = pg_insert(SavedReportMetricModel).values(
                [{"relatorio_salvo_id": saved_report.id, "metrica_id": mid} for mid in saved_report.metricas_ids]
            ).on_conflict_do_nothing(index_elements=["relatorio_salvo_id", "metrica_id"])
            await self._session.execute(stmt)
        await self._session.flush()
