from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.collection import Collection
from modules.freight.domain.repositories.collection_repository import CollectionRepository
from modules.freight.infrastructure.persistence.models.collection_model import CollectionModel


class SqlAlchemyCollectionRepository(CollectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_for_trip(self, viagem_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(CollectionModel.id).where(
            CollectionModel.tenant_id == tenant_id, CollectionModel.viagem_id == viagem_id
        )
        return (await self._session.execute(stmt)).first() is not None

    async def create(self, collection: Collection) -> None:
        tenant_id = get_current_tenant_id()
        model = CollectionModel(
            id=collection.id, tenant_id=tenant_id, viagem_id=collection.viagem_id, data_hora=collection.data_hora,
            conferencia_ok=collection.conferencia_ok,
        )
        self._session.add(model)
        await self._session.flush()
