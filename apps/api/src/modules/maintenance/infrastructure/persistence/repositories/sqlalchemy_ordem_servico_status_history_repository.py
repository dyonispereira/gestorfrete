from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.repositories.ordem_servico_status_history_repository import (
    OrdemServicoStatusHistoryRepository,
)
from modules.maintenance.infrastructure.persistence.models.ordem_servico_model import (
    OrdemServicoStatusHistoryModel,
)


def _to_entity(model: OrdemServicoStatusHistoryModel) -> OrdemServicoStatusHistoryEntry:
    return OrdemServicoStatusHistoryEntry(
        id=model.id, ordem_servico_id=model.ordem_servico_id, status=model.status, usuario_id=model.usuario_id,
        origem=model.origem, observacao=model.observacao, data_hora=model.data_hora,
    )


class SqlAlchemyOrdemServicoStatusHistoryRepository(OrdemServicoStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: OrdemServicoStatusHistoryEntry) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            OrdemServicoStatusHistoryModel(
                id=entry.id, tenant_id=tenant_id, ordem_servico_id=entry.ordem_servico_id, status=entry.status,
                usuario_id=entry.usuario_id, origem=entry.origem, observacao=entry.observacao,
                data_hora=entry.data_hora,
            )
        )
        await self._session.flush()

    async def list_page(
        self, ordem_servico_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[OrdemServicoStatusHistoryEntry]:
        tenant_id = get_current_tenant_id()
        stmt = select(OrdemServicoStatusHistoryModel).where(
            OrdemServicoStatusHistoryModel.tenant_id == tenant_id,
            OrdemServicoStatusHistoryModel.ordem_servico_id == ordem_servico_id,
        )
        if status is not None:
            stmt = stmt.where(OrdemServicoStatusHistoryModel.status == status)
        if after_data_hora is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    OrdemServicoStatusHistoryModel.data_hora < after_data_hora,
                    and_(
                        OrdemServicoStatusHistoryModel.data_hora == after_data_hora,
                        OrdemServicoStatusHistoryModel.id < after_id,
                    ),
                )
            )
        stmt = stmt.order_by(
            OrdemServicoStatusHistoryModel.data_hora.desc(), OrdemServicoStatusHistoryModel.id.desc()
        ).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
