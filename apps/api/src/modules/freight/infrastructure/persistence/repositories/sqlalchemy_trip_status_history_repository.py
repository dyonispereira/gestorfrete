from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.repositories.trip_status_history_repository import TripStatusHistoryRepository
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.models.trip_status_history_model import TripStatusHistoryModel


def _to_entity(model: TripStatusHistoryModel) -> TripStatusHistoryEntry:
    return TripStatusHistoryEntry(
        id=model.id,
        viagem_id=model.viagem_id,
        dimensao=StatusHistoryDimension(model.dimensao),
        status=model.status,
        usuario_id=model.usuario_id,
        origem=model.origem,
        data_hora=model.data_hora,
        observacao=model.observacao,
        latitude=model.latitude,
        longitude=model.longitude,
    )


class SqlAlchemyTripStatusHistoryRepository(TripStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: TripStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        model = TripStatusHistoryModel(
            id=entry.id,
            tenant_id=tenant_id,
            viagem_id=entry.viagem_id,
            dimensao=entry.dimensao.value,
            status=entry.status,
            usuario_id=entry.usuario_id,
            origem=entry.origem,
            data_hora=entry.data_hora,
            observacao=entry.observacao,
            latitude=entry.latitude,
            longitude=entry.longitude,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_last_operational_before(self, viagem_id: uuid.UUID, before: datetime) -> TripStatusHistoryEntry | None:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(TripStatusHistoryModel)
            .where(
                TripStatusHistoryModel.tenant_id == tenant_id,
                TripStatusHistoryModel.viagem_id == viagem_id,
                TripStatusHistoryModel.dimensao == StatusHistoryDimension.OPERACIONAL.value,
                TripStatusHistoryModel.data_hora < before,
                TripStatusHistoryModel.status != TripOperationalStatus.INTERROMPIDA.value,
            )
            .order_by(TripStatusHistoryModel.data_hora.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_accepted(self, viagem_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(TripStatusHistoryModel.id).where(
            TripStatusHistoryModel.tenant_id == tenant_id,
            TripStatusHistoryModel.viagem_id == viagem_id,
            TripStatusHistoryModel.origem == "app_motorista",
            TripStatusHistoryModel.status == TripOperationalStatus.PLANEJADA.value,
            TripStatusHistoryModel.dimensao == StatusHistoryDimension.OPERACIONAL.value,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_for_trip_cursor(
        self,
        viagem_id: uuid.UUID,
        *,
        dimensao: StatusHistoryDimension | None,
        limit: int,
        after_data_hora: datetime | None,
        after_id: uuid.UUID | None,
    ) -> list[TripStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = select(TripStatusHistoryModel).where(
            TripStatusHistoryModel.tenant_id == tenant_id, TripStatusHistoryModel.viagem_id == viagem_id
        )
        if dimensao is not None:
            stmt = stmt.where(TripStatusHistoryModel.dimensao == dimensao.value)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    TripStatusHistoryModel.data_hora < after_data_hora,
                    and_(TripStatusHistoryModel.data_hora == after_data_hora, TripStatusHistoryModel.id < after_id),
                )
            )
        stmt = stmt.order_by(TripStatusHistoryModel.data_hora.desc(), TripStatusHistoryModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
