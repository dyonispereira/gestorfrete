from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.receivable_status_history_entry import ReceivableStatusHistoryEntry
from modules.financial.domain.repositories.receivable_status_history_repository import (
    ReceivableStatusHistoryRepository,
)
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.models.accounts_receivable_model import ReceivableStatusHistoryModel


def _to_entity(model: ReceivableStatusHistoryModel) -> ReceivableStatusHistoryEntry:
    return ReceivableStatusHistoryEntry(
        id=model.id, conta_receber_id=model.conta_receber_id, status=ReceivableStatus(model.status),
        usuario_id=model.usuario_id, data_hora=model.data_hora,
    )


class SqlAlchemyReceivableStatusHistoryRepository(ReceivableStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: ReceivableStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        model = ReceivableStatusHistoryModel(
            id=entry.id, tenant_id=tenant_id, conta_receber_id=entry.conta_receber_id, status=entry.status.value,
            usuario_id=entry.usuario_id, data_hora=entry.data_hora,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_for_receivable(self, conta_receber_id: uuid.UUID) -> list[ReceivableStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(ReceivableStatusHistoryModel)
            .where(
                ReceivableStatusHistoryModel.tenant_id == tenant_id,
                ReceivableStatusHistoryModel.conta_receber_id == conta_receber_id,
            )
            .order_by(ReceivableStatusHistoryModel.data_hora)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
