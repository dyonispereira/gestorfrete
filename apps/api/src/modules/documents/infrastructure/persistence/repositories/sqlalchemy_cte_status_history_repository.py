from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.cte_status_history_entry import CteStatusHistoryEntry
from modules.documents.domain.repositories.cte_status_history_repository import CteStatusHistoryRepository
from modules.documents.infrastructure.persistence.models.cte_model import CteStatusHistoryModel


def _to_entity(model: CteStatusHistoryModel) -> CteStatusHistoryEntry:
    return CteStatusHistoryEntry(
        id=model.id, cte_id=model.cte_id, status=model.status, usuario_id=model.usuario_id,
        origem=model.origem, observacao=model.observacao, data_hora=model.data_hora,
    )


class SqlAlchemyCteStatusHistoryRepository(CteStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: CteStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            CteStatusHistoryModel(
                id=entry.id, tenant_id=tenant_id, cte_id=entry.cte_id, status=entry.status,
                usuario_id=entry.usuario_id, origem=entry.origem, observacao=entry.observacao,
                data_hora=entry.data_hora,
            )
        )
        await self._session.flush()

    async def count_for_cte(self, cte_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(func.count()).select_from(CteStatusHistoryModel).where(
            CteStatusHistoryModel.tenant_id == tenant_id, CteStatusHistoryModel.cte_id == cte_id
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def list_page(
        self, cte_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[CteStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = select(CteStatusHistoryModel).where(
            CteStatusHistoryModel.tenant_id == tenant_id, CteStatusHistoryModel.cte_id == cte_id
        )
        if status is not None:
            stmt = stmt.where(CteStatusHistoryModel.status == status)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    CteStatusHistoryModel.data_hora < after_data_hora,
                    and_(CteStatusHistoryModel.data_hora == after_data_hora, CteStatusHistoryModel.id < after_id),
                )
            )
        stmt = stmt.order_by(CteStatusHistoryModel.data_hora.desc(), CteStatusHistoryModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
