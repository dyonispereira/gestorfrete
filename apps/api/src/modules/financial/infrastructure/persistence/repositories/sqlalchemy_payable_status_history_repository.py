from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry
from modules.financial.domain.repositories.payable_status_history_repository import PayableStatusHistoryRepository
from modules.financial.domain.value_objects.payable_status import PayableStatus
from modules.financial.infrastructure.persistence.models.accounts_payable_model import PayableStatusHistoryModel


def _to_entity(model: PayableStatusHistoryModel) -> PayableStatusHistoryEntry:
    return PayableStatusHistoryEntry(
        id=model.id, conta_pagar_id=model.conta_pagar_id, status=PayableStatus(model.status),
        usuario_id=model.usuario_id, observacao=model.observacao, data_hora=model.data_hora,
    )


class SqlAlchemyPayableStatusHistoryRepository(PayableStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: PayableStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        model = PayableStatusHistoryModel(
            id=entry.id, tenant_id=tenant_id, conta_pagar_id=entry.conta_pagar_id, status=entry.status.value,
            usuario_id=entry.usuario_id, observacao=entry.observacao, data_hora=entry.data_hora,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[PayableStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(PayableStatusHistoryModel)
            .where(
                PayableStatusHistoryModel.tenant_id == tenant_id,
                PayableStatusHistoryModel.conta_pagar_id == conta_pagar_id,
            )
            .order_by(PayableStatusHistoryModel.data_hora)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
