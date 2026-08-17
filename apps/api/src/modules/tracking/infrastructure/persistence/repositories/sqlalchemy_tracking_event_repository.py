from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.tracking_event import TrackingEvent
from modules.tracking.domain.repositories.tracking_event_repository import TrackingEventRepository
from modules.tracking.domain.value_objects.tracking_event_severity import TrackingEventSeverity
from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType
from modules.tracking.infrastructure.persistence.models.tracking_event_model import TrackingEventModel


def _to_entity(model: TrackingEventModel) -> TrackingEvent:
    return TrackingEvent(
        id=model.id, veiculo_tracionador_id=model.veiculo_tracionador_id, tipo=TrackingEventType(model.tipo),
        posicao_veiculo_id=model.posicao_veiculo_id, cerca_eletronica_id=model.cerca_eletronica_id,
        configuracao_limite_velocidade_id=model.configuracao_limite_velocidade_id,
        valor_detectado=float(model.valor_detectado) if model.valor_detectado is not None else None,
        severidade=TrackingEventSeverity(model.severidade), data_hora=model.data_hora,
    )


class SqlAlchemyTrackingEventRepository(TrackingEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> TrackingEvent | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEventModel).where(
            TrackingEventModel.id == id, TrackingEventModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, event: TrackingEvent) -> None:
        tenant_id = get_current_tenant_id()
        model = TrackingEventModel(
            id=event.id, tenant_id=tenant_id, veiculo_tracionador_id=event.veiculo_tracionador_id,
            tipo=event.tipo.value, posicao_veiculo_id=event.posicao_veiculo_id,
            cerca_eletronica_id=event.cerca_eletronica_id,
            configuracao_limite_velocidade_id=event.configuracao_limite_velocidade_id,
            valor_detectado=event.valor_detectado, severidade=event.severidade.value, data_hora=event.data_hora,
        )
        self._session.add(model)
        await self._session.flush()

    async def exists_referencing_geofence(self, cerca_eletronica_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEventModel.id).where(
            TrackingEventModel.tenant_id == tenant_id, TrackingEventModel.cerca_eletronica_id == cerca_eletronica_id
        ).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, after_data_hora: datetime | None, after_id: uuid.UUID | None, limit: int,
        types: list[str] | None, severity: str | None, vehicle_id: uuid.UUID | None,
        occurred_at_gte: datetime | None, occurred_at_lte: datetime | None,
    ) -> list[TrackingEvent]:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEventModel).where(TrackingEventModel.tenant_id == tenant_id)
        if types is not None:
            stmt = stmt.where(TrackingEventModel.tipo.in_(types))
        if severity is not None:
            stmt = stmt.where(TrackingEventModel.severidade == severity)
        if vehicle_id is not None:
            stmt = stmt.where(TrackingEventModel.veiculo_tracionador_id == vehicle_id)
        if occurred_at_gte is not None:
            stmt = stmt.where(TrackingEventModel.data_hora >= occurred_at_gte)
        if occurred_at_lte is not None:
            stmt = stmt.where(TrackingEventModel.data_hora <= occurred_at_lte)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    TrackingEventModel.data_hora < after_data_hora,
                    and_(TrackingEventModel.data_hora == after_data_hora, TrackingEventModel.id < after_id),
                )
            )
        stmt = stmt.order_by(TrackingEventModel.data_hora.desc(), TrackingEventModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
