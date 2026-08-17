from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.mdfe_status_history_entry import MdfeStatusHistoryEntry
from modules.documents.domain.repositories.mdfe_status_history_repository import MdfeStatusHistoryRepository
from modules.documents.infrastructure.persistence.models.mdfe_model import MdfeStatusHistoryModel


def _to_entity(model: MdfeStatusHistoryModel) -> MdfeStatusHistoryEntry:
    return MdfeStatusHistoryEntry(
        id=model.id, mdfe_id=model.mdfe_id, status=model.status, usuario_id=model.usuario_id,
        origem=model.origem, observacao=model.observacao, data_hora=model.data_hora,
    )


class SqlAlchemyMdfeStatusHistoryRepository(MdfeStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: MdfeStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            MdfeStatusHistoryModel(
                id=entry.id, tenant_id=tenant_id, mdfe_id=entry.mdfe_id, status=entry.status,
                usuario_id=entry.usuario_id, origem=entry.origem, observacao=entry.observacao,
                data_hora=entry.data_hora,
            )
        )
        await self._session.flush()

    async def count_for_mdfe(self, mdfe_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(func.count()).select_from(MdfeStatusHistoryModel).where(
            MdfeStatusHistoryModel.tenant_id == tenant_id, MdfeStatusHistoryModel.mdfe_id == mdfe_id
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def list_page(
        self, mdfe_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[MdfeStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = select(MdfeStatusHistoryModel).where(
            MdfeStatusHistoryModel.tenant_id == tenant_id, MdfeStatusHistoryModel.mdfe_id == mdfe_id
        )
        if status is not None:
            stmt = stmt.where(MdfeStatusHistoryModel.status == status)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    MdfeStatusHistoryModel.data_hora < after_data_hora,
                    and_(MdfeStatusHistoryModel.data_hora == after_data_hora, MdfeStatusHistoryModel.id < after_id),
                )
            )
        stmt = stmt.order_by(MdfeStatusHistoryModel.data_hora.desc(), MdfeStatusHistoryModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
