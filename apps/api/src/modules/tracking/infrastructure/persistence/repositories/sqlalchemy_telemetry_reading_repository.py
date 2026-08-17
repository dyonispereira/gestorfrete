from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.telemetry_reading import TelemetryReading
from modules.tracking.domain.repositories.telemetry_reading_repository import TelemetryReadingRepository
from modules.tracking.domain.value_objects.sensor_type import SensorType
from modules.tracking.infrastructure.persistence.models.telemetry_reading_model import TelemetryReadingModel


def _to_entity(model: TelemetryReadingModel) -> TelemetryReading:
    return TelemetryReading(
        id=model.id, veiculo_tracionador_id=model.veiculo_tracionador_id,
        equipamento_rastreamento_id=model.equipamento_rastreamento_id, posicao_veiculo_id=model.posicao_veiculo_id,
        tipo_sensor=SensorType(model.tipo_sensor), valor=float(model.valor), unidade=model.unidade,
        capturado_em=model.capturado_em, recebido_em=model.recebido_em, processado_em=model.processado_em,
    )


class SqlAlchemyTelemetryReadingRepository(TelemetryReadingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, reading: TelemetryReading) -> None:
        tenant_id = get_current_tenant_id()
        model = TelemetryReadingModel(
            id=reading.id, tenant_id=tenant_id, veiculo_tracionador_id=reading.veiculo_tracionador_id,
            equipamento_rastreamento_id=reading.equipamento_rastreamento_id,
            posicao_veiculo_id=reading.posicao_veiculo_id, tipo_sensor=reading.tipo_sensor.value,
            valor=reading.valor, unidade=reading.unidade, capturado_em=reading.capturado_em,
            recebido_em=reading.recebido_em, processado_em=reading.processado_em,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, after_capturado_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, sensor_type: str | None,
        captured_at_gte: datetime | None, captured_at_lte: datetime | None, equipment_id: uuid.UUID | None,
    ) -> list[TelemetryReading]:
        tenant_id = get_current_tenant_id()
        stmt = select(TelemetryReadingModel).where(
            TelemetryReadingModel.tenant_id == tenant_id,
            TelemetryReadingModel.veiculo_tracionador_id == veiculo_tracionador_id,
        )
        if sensor_type is not None:
            stmt = stmt.where(TelemetryReadingModel.tipo_sensor == sensor_type)
        if captured_at_gte is not None:
            stmt = stmt.where(TelemetryReadingModel.capturado_em >= captured_at_gte)
        if captured_at_lte is not None:
            stmt = stmt.where(TelemetryReadingModel.capturado_em <= captured_at_lte)
        if equipment_id is not None:
            stmt = stmt.where(TelemetryReadingModel.equipamento_rastreamento_id == equipment_id)
        if after_capturado_em is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    TelemetryReadingModel.capturado_em < after_capturado_em,
                    and_(
                        TelemetryReadingModel.capturado_em == after_capturado_em,
                        TelemetryReadingModel.id < after_id,
                    ),
                )
            )
        stmt = stmt.order_by(TelemetryReadingModel.capturado_em.desc(), TelemetryReadingModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
