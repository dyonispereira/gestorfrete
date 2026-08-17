from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.heartbeat import Heartbeat
from modules.tracking.domain.repositories.heartbeat_repository import HeartbeatRepository
from modules.tracking.infrastructure.persistence.models.heartbeat_model import HeartbeatModel


def _to_entity(model: HeartbeatModel) -> Heartbeat:
    return Heartbeat(
        id=model.id, equipamento_rastreamento_id=model.equipamento_rastreamento_id,
        protocolo_externo=model.protocolo_externo, capturado_em=model.capturado_em,
        recebido_em=model.recebido_em, processado_em=model.processado_em,
    )


class SqlAlchemyHeartbeatRepository(HeartbeatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, heartbeat: Heartbeat) -> None:
        tenant_id = get_current_tenant_id()
        model = HeartbeatModel(
            id=heartbeat.id, tenant_id=tenant_id, equipamento_rastreamento_id=heartbeat.equipamento_rastreamento_id,
            protocolo_externo=heartbeat.protocolo_externo, capturado_em=heartbeat.capturado_em,
            recebido_em=heartbeat.recebido_em, processado_em=heartbeat.processado_em,
        )
        self._session.add(model)
        await self._session.flush()

    async def exists_with_protocol(self, equipamento_rastreamento_id: uuid.UUID, protocolo_externo: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(HeartbeatModel.id).where(
            HeartbeatModel.tenant_id == tenant_id,
            HeartbeatModel.equipamento_rastreamento_id == equipamento_rastreamento_id,
            HeartbeatModel.protocolo_externo == protocolo_externo,
        ).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, equipamento_rastreamento_id: uuid.UUID, after_recebido_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, received_at_gte: datetime | None,
        received_at_lte: datetime | None,
    ) -> list[Heartbeat]:
        tenant_id = get_current_tenant_id()
        stmt = select(HeartbeatModel).where(
            HeartbeatModel.tenant_id == tenant_id,
            HeartbeatModel.equipamento_rastreamento_id == equipamento_rastreamento_id,
        )
        if received_at_gte is not None:
            stmt = stmt.where(HeartbeatModel.recebido_em >= received_at_gte)
        if received_at_lte is not None:
            stmt = stmt.where(HeartbeatModel.recebido_em <= received_at_lte)
        if after_recebido_em is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    HeartbeatModel.recebido_em < after_recebido_em,
                    and_(HeartbeatModel.recebido_em == after_recebido_em, HeartbeatModel.id < after_id),
                )
            )
        stmt = stmt.order_by(HeartbeatModel.recebido_em.desc(), HeartbeatModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
