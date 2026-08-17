from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.referenced_nfe import ReferencedNfe
from modules.documents.domain.repositories.referenced_nfe_repository import ReferencedNfeRepository
from modules.documents.infrastructure.persistence.models.referenced_nfe_model import ReferencedNfeModel


def _to_entity(model: ReferencedNfeModel) -> ReferencedNfe:
    return ReferencedNfe(id=model.id, cte_id=model.cte_id, chave_acesso=model.chave_acesso, xml_arquivo_id=model.xml_arquivo_id)


class SqlAlchemyReferencedNfeRepository(ReferencedNfeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ReferencedNfe | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ReferencedNfeModel).where(
            ReferencedNfeModel.id == id, ReferencedNfeModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_cte(self, cte_id: uuid.UUID) -> list[ReferencedNfe]:
        tenant_id = get_current_tenant_id()
        stmt = select(ReferencedNfeModel).where(
            ReferencedNfeModel.tenant_id == tenant_id, ReferencedNfeModel.cte_id == cte_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, nfe: ReferencedNfe) -> None:
        tenant_id = get_current_tenant_id()
        model = ReferencedNfeModel(
            id=nfe.id, tenant_id=tenant_id, cte_id=nfe.cte_id, chave_acesso=nfe.chave_acesso,
            xml_arquivo_id=nfe.xml_arquivo_id,
        )
        self._session.add(model)
        await self._session.flush()
