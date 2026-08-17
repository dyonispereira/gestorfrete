from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.odometer_reading import OdometerReading
from modules.fleet.domain.repositories.odometer_reading_repository import OdometerReadingRepository
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.fleet.infrastructure.persistence.models.odometer_reading_model import OdometerReadingModel


def _to_entity(model: OdometerReadingModel) -> OdometerReading:
    return OdometerReading(
        id=model.id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        valor_km=model.valor_km,
        origem=OdometerOrigin(model.origem),
        viagem_id=model.viagem_id,
        data_hora=model.data_hora,
    )


class SqlAlchemyOdometerReadingRepository(OdometerReadingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> OdometerReading | None:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(OdometerReadingModel)
            .where(
                OdometerReadingModel.tenant_id == tenant_id,
                OdometerReadingModel.veiculo_tracionador_id == veiculo_tracionador_id,
            )
            .order_by(OdometerReadingModel.data_hora.desc(), OdometerReadingModel.id.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_vehicle_cursor(
        self,
        *,
        veiculo_tracionador_id: uuid.UUID,
        limit: int,
        origem: str | None,
        after_data_hora: datetime | None,
        after_id: uuid.UUID | None,
    ) -> list[OdometerReading]:
        tenant_id = get_current_tenant_id()
        stmt = select(OdometerReadingModel).where(
            OdometerReadingModel.tenant_id == tenant_id,
            OdometerReadingModel.veiculo_tracionador_id == veiculo_tracionador_id,
        )
        if origem is not None:
            stmt = stmt.where(OdometerReadingModel.origem == origem)
        if after_data_hora is not None and after_id is not None:
            # Mesma coluna de corte do índice (`data_hora DESC`) — cursor nunca reinventa uma
            # ordenação diferente (`PAGINATION.md`).
            stmt = stmt.where(
                or_(
                    OdometerReadingModel.data_hora < after_data_hora,
                    and_(OdometerReadingModel.data_hora == after_data_hora, OdometerReadingModel.id < after_id),
                )
            )
        stmt = stmt.order_by(OdometerReadingModel.data_hora.desc(), OdometerReadingModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, reading: OdometerReading) -> None:
        tenant_id = get_current_tenant_id()
        model = OdometerReadingModel(
            id=reading.id,
            tenant_id=tenant_id,
            veiculo_tracionador_id=reading.veiculo_tracionador_id,
            valor_km=reading.valor_km,
            origem=reading.origem.value,
            viagem_id=reading.viagem_id,
            data_hora=reading.data_hora,
        )
        self._session.add(model)
        await self._session.flush()
