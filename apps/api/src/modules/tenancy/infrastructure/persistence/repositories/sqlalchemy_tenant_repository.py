from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.tenancy.domain.entities.tenant import Tenant
from modules.tenancy.domain.repositories.tenant_repository import TenantRepository
from modules.tenancy.domain.value_objects.tenant_status import TenantStatus
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.audit_metadata import AuditMetadata


def _to_entity(model: TenantModel) -> Tenant:
    return Tenant(
        id=model.id,
        codigo=model.codigo,
        versao=model.versao,
        razao_social=model.razao_social,
        cnpj=model.cnpj,
        status=TenantStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyTenantRepository(TenantRepository):
    """D341 — nunca decide autorização, só resolve dados; sempre filtra `excluido_em IS NULL`
    (D343) exceto onde explicitamente documentado o contrário (nenhum caso neste bounded context
    ainda)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Tenant | None:
        stmt = select(TenantModel).where(
            TenantModel.id == id, TenantModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, aggregate: Tenant) -> None:
        model = await self._session.get(TenantModel, aggregate.id)
        if model is None:
            model = TenantModel(id=aggregate.id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.versao = aggregate.versao
        model.razao_social = aggregate.razao_social
        model.cnpj = aggregate.cnpj
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by

    async def exists_with_cnpj(self, cnpj: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        stmt = select(TenantModel.id).where(TenantModel.cnpj == cnpj)
        if excluding_id is not None:
            stmt = stmt.where(TenantModel.id != excluding_id)
        result = (await self._session.execute(stmt)).first()
        return result is not None
