from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.integration.domain.entities.job_execution import JobExecution
from modules.integration.domain.repositories.job_execution_repository import JobExecutionRepository
from modules.integration.domain.value_objects.job_result import JobResult
from modules.integration.infrastructure.persistence.models.job_execution_model import JobExecutionModel


def _to_entity(model: JobExecutionModel) -> JobExecution:
    return JobExecution(
        id=model.id, tenant_id=model.tenant_id, tipo_job=model.tipo_job, data_hora_inicio=model.data_hora_inicio,
        data_hora_fim=model.data_hora_fim, resultado=JobResult(model.resultado) if model.resultado else None,
    )


class SqlAlchemyJobExecutionRepository(JobExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> JobExecution | None:
        tenant_id = get_current_tenant_id()
        stmt = select(JobExecutionModel).where(JobExecutionModel.id == id, JobExecutionModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_cursor(
        self, *, limit: int, job_type: str | None, result: str | None, started_from: datetime | None,
        started_to: datetime | None, after_data_hora_inicio: datetime | None, after_id: uuid.UUID | None,
    ) -> list[JobExecution]:
        tenant_id = get_current_tenant_id()
        stmt = select(JobExecutionModel).where(JobExecutionModel.tenant_id == tenant_id)
        if job_type is not None:
            stmt = stmt.where(JobExecutionModel.tipo_job == job_type)
        if result is not None:
            stmt = stmt.where(JobExecutionModel.resultado == result)
        if started_from is not None:
            stmt = stmt.where(JobExecutionModel.data_hora_inicio >= started_from)
        if started_to is not None:
            stmt = stmt.where(JobExecutionModel.data_hora_inicio <= started_to)
        if after_data_hora_inicio is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    JobExecutionModel.data_hora_inicio < after_data_hora_inicio,
                    and_(
                        JobExecutionModel.data_hora_inicio == after_data_hora_inicio,
                        JobExecutionModel.id < after_id,
                    ),
                )
            )

        stmt = stmt.order_by(JobExecutionModel.data_hora_inicio.desc(), JobExecutionModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, execution: JobExecution) -> None:
        model = await self._session.get(
            JobExecutionModel, {"id": execution.id, "data_hora_inicio": execution.data_hora_inicio}
        )
        if model is None:
            model = JobExecutionModel(
                id=execution.id, tenant_id=execution.tenant_id, data_hora_inicio=execution.data_hora_inicio
            )
            self._session.add(model)
        model.tipo_job = execution.tipo_job
        model.data_hora_fim = execution.data_hora_fim
        model.resultado = execution.resultado.value if execution.resultado else None
        await self._session.flush()
