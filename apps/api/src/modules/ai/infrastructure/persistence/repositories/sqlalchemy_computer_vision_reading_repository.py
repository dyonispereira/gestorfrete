from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.computer_vision_reading import ComputerVisionReading
from modules.ai.domain.repositories.computer_vision_reading_repository import ComputerVisionReadingRepository
from modules.ai.domain.value_objects.computer_vision_reading_status import ComputerVisionReadingStatus
from modules.ai.domain.value_objects.reading_type import ReadingType
from modules.ai.infrastructure.persistence.models.computer_vision_reading_model import ComputerVisionReadingModel


def _to_entity(model: ComputerVisionReadingModel) -> ComputerVisionReading:
    return ComputerVisionReading(
        id=model.id, tenant_id=model.tenant_id, inferencia_ia_id=model.inferencia_ia_id,
        arquivo_origem_id=model.arquivo_origem_id, tipo_leitura=ReadingType(model.tipo_leitura),
        regiao_analisada=model.regiao_analisada, resultado_extraido=model.resultado_extraido,
        nivel_confianca=model.nivel_confianca, revisao_humana_necessaria=model.revisao_humana_necessaria,
        status=ComputerVisionReadingStatus(model.status), usuario_confirmacao_id=model.usuario_confirmacao_id,
    )


class SqlAlchemyComputerVisionReadingRepository(ComputerVisionReadingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ComputerVisionReading | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ComputerVisionReadingModel).where(
            ComputerVisionReadingModel.id == id, ComputerVisionReadingModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, tipo_leitura: str | None, status: str | None,
        revisao_humana_necessaria: bool | None,
    ) -> tuple[list[ComputerVisionReading], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ComputerVisionReadingModel).where(ComputerVisionReadingModel.tenant_id == tenant_id)
        if tipo_leitura is not None:
            stmt = stmt.where(ComputerVisionReadingModel.tipo_leitura == tipo_leitura)
        if status is not None:
            stmt = stmt.where(ComputerVisionReadingModel.status == status)
        if revisao_humana_necessaria is not None:
            stmt = stmt.where(ComputerVisionReadingModel.revisao_humana_necessaria == revisao_humana_necessaria)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ComputerVisionReadingModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, reading: ComputerVisionReading) -> None:
        model = await self._session.get(ComputerVisionReadingModel, reading.id)
        if model is None:
            model = ComputerVisionReadingModel(id=reading.id, tenant_id=reading.tenant_id)
            self._session.add(model)
        model.inferencia_ia_id = reading.inferencia_ia_id
        model.arquivo_origem_id = reading.arquivo_origem_id
        model.tipo_leitura = reading.tipo_leitura.value
        model.regiao_analisada = reading.regiao_analisada
        model.resultado_extraido = reading.resultado_extraido
        model.nivel_confianca = reading.nivel_confianca
        model.revisao_humana_necessaria = reading.revisao_humana_necessaria
        model.status = reading.status.value
        model.usuario_confirmacao_id = reading.usuario_confirmacao_id
        await self._session.flush()
