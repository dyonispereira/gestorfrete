from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.mobile.domain.entities.sync_queue_item import SyncQueueItem
from modules.mobile.domain.repositories.sync_queue_item_repository import SyncQueueItemRepository
from modules.mobile.domain.value_objects.sync_item_status import SyncItemStatus
from modules.mobile.infrastructure.persistence.models.sync_queue_item_model import SyncQueueItemModel


def _to_entity(model: SyncQueueItemModel) -> SyncQueueItem:
    return SyncQueueItem(
        id=model.id, sessao_mobile_id=model.sessao_mobile_id, sequencia_local=model.sequencia_local,
        tipo_comando=model.tipo_comando, entidade_destino_tipo=model.entidade_destino_tipo,
        entidade_destino_id=model.entidade_destino_id, payload=model.payload,
        identificador_local_unico=model.identificador_local_unico, numero_tentativa=model.numero_tentativa,
        status=SyncItemStatus(model.status), resolucao_conflito=model.resolucao_conflito, criado_em=model.criado_em,
    )


class SqlAlchemySyncQueueItemRepository(SyncQueueItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_local_id(
        self, sessao_mobile_id: uuid.UUID, identificador_local_unico: str
    ) -> SyncQueueItem | None:
        tenant_id = get_current_tenant_id()
        stmt = select(SyncQueueItemModel).where(
            SyncQueueItemModel.tenant_id == tenant_id, SyncQueueItemModel.sessao_mobile_id == sessao_mobile_id,
            SyncQueueItemModel.identificador_local_unico == identificador_local_unico,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add_if_absent(self, item: SyncQueueItem) -> SyncQueueItem:
        tenant_id = get_current_tenant_id()
        stmt = pg_insert(SyncQueueItemModel).values(
            id=item.id, tenant_id=tenant_id, sessao_mobile_id=item.sessao_mobile_id,
            sequencia_local=item.sequencia_local, tipo_comando=item.tipo_comando,
            entidade_destino_tipo=item.entidade_destino_tipo, entidade_destino_id=item.entidade_destino_id,
            payload=item.payload, identificador_local_unico=item.identificador_local_unico,
            numero_tentativa=item.numero_tentativa, status=item.status.value, criado_em=item.criado_em,
        ).on_conflict_do_nothing(index_elements=["sessao_mobile_id", "identificador_local_unico"])
        await self._session.execute(stmt)
        await self._session.flush()

        existing = await self.get_by_local_id(item.sessao_mobile_id, item.identificador_local_unico)
        assert existing is not None
        return existing

    async def update(self, item: SyncQueueItem) -> None:
        model = await self._session.get(SyncQueueItemModel, item.id)
        assert model is not None
        model.numero_tentativa = item.numero_tentativa
        model.status = item.status.value
        model.resolucao_conflito = item.resolucao_conflito
        await self._session.flush()

    async def list_pending_ordered(self, sessao_mobile_id: uuid.UUID) -> list[SyncQueueItem]:
        tenant_id = get_current_tenant_id()
        stmt = select(SyncQueueItemModel).where(
            SyncQueueItemModel.tenant_id == tenant_id, SyncQueueItemModel.sessao_mobile_id == sessao_mobile_id,
            SyncQueueItemModel.status.in_([SyncItemStatus.PENDENTE.value, SyncItemStatus.FALHOU.value]),
        ).order_by(SyncQueueItemModel.sequencia_local.asc())
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
