from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.manifest import Manifest
from modules.freight.domain.repositories.manifest_repository import ManifestRepository
from modules.freight.infrastructure.persistence.models.manifest_model import CargoItemModel, ManifestModel


class SqlAlchemyManifestRepository(ManifestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_for_trip(self, viagem_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ManifestModel.id).where(ManifestModel.tenant_id == tenant_id, ManifestModel.viagem_id == viagem_id)
        return (await self._session.execute(stmt)).first() is not None

    async def create(self, manifest: Manifest) -> None:
        tenant_id = get_current_tenant_id()
        model = ManifestModel(
            id=manifest.id, tenant_id=tenant_id, viagem_id=manifest.viagem_id,
            numero_documento=manifest.numero_documento,
        )
        self._session.add(model)
        await self._session.flush()  # Romaneio precisa existir antes dos Itens de Carga (FK)
        for item in manifest.itens:
            self._session.add(
                CargoItemModel(
                    id=item.id, tenant_id=tenant_id, romaneio_id=manifest.id, descricao=item.descricao,
                    peso=item.peso, quantidade=item.quantidade,
                )
            )
        await self._session.flush()
