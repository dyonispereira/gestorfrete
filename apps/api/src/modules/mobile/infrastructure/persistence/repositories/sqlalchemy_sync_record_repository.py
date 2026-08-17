from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.mobile.domain.entities.sync_record import SyncRecord
from modules.mobile.domain.repositories.sync_record_repository import SyncRecordRepository
from modules.mobile.infrastructure.persistence.models.sync_record_model import SyncRecordModel


def _to_entity(model: SyncRecordModel) -> SyncRecord:
    return SyncRecord(
        id=model.id, sessao_mobile_id=model.sessao_mobile_id, data_hora_inicio=model.data_hora_inicio,
        data_hora_fim=model.data_hora_fim, quantidade_comandos=model.quantidade_comandos,
        quantidade_sucesso=model.quantidade_sucesso, quantidade_falha=model.quantidade_falha,
    )


class SqlAlchemySyncRecordRepository(SyncRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, record: SyncRecord) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            SyncRecordModel(
                id=record.id, tenant_id=tenant_id, sessao_mobile_id=record.sessao_mobile_id,
                data_hora_inicio=record.data_hora_inicio, data_hora_fim=record.data_hora_fim,
                quantidade_comandos=record.quantidade_comandos, quantidade_sucesso=record.quantidade_sucesso,
                quantidade_falha=record.quantidade_falha,
            )
        )
        await self._session.flush()

    async def list_page(
        self, *, sessao_mobile_id: uuid.UUID | None, page: int, limit: int
    ) -> tuple[list[SyncRecord], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(SyncRecordModel).where(SyncRecordModel.tenant_id == tenant_id)
        if sessao_mobile_id is not None:
            stmt = stmt.where(SyncRecordModel.sessao_mobile_id == sessao_mobile_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SyncRecordModel.data_hora_inicio.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total
