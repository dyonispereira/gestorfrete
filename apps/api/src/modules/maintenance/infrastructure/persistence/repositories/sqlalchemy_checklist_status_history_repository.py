from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry
from modules.maintenance.domain.repositories.checklist_status_history_repository import (
    ChecklistStatusHistoryRepository,
)
from modules.maintenance.infrastructure.persistence.models.checklist_model import ChecklistStatusHistoryModel


def _to_entity(model: ChecklistStatusHistoryModel) -> ChecklistStatusHistoryEntry:
    return ChecklistStatusHistoryEntry(
        id=model.id, checklist_id=model.checklist_id, status=model.status, usuario_id=model.usuario_id,
        origem=model.origem, observacao=model.observacao, data_hora=model.data_hora,
    )


class SqlAlchemyChecklistStatusHistoryRepository(ChecklistStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: ChecklistStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            ChecklistStatusHistoryModel(
                id=entry.id, tenant_id=tenant_id, checklist_id=entry.checklist_id, status=entry.status,
                usuario_id=entry.usuario_id, origem=entry.origem, observacao=entry.observacao,
                data_hora=entry.data_hora,
            )
        )
        await self._session.flush()

    async def count_for_checklist(self, checklist_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(func.count()).select_from(ChecklistStatusHistoryModel).where(
            ChecklistStatusHistoryModel.tenant_id == tenant_id, ChecklistStatusHistoryModel.checklist_id == checklist_id
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def list_page(
        self, checklist_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[ChecklistStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = select(ChecklistStatusHistoryModel).where(
            ChecklistStatusHistoryModel.tenant_id == tenant_id, ChecklistStatusHistoryModel.checklist_id == checklist_id
        )
        if status is not None:
            stmt = stmt.where(ChecklistStatusHistoryModel.status == status)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    ChecklistStatusHistoryModel.data_hora < after_data_hora,
                    and_(
                        ChecklistStatusHistoryModel.data_hora == after_data_hora,
                        ChecklistStatusHistoryModel.id < after_id,
                    ),
                )
            )
        stmt = stmt.order_by(
            ChecklistStatusHistoryModel.data_hora.desc(), ChecklistStatusHistoryModel.id.desc()
        ).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
