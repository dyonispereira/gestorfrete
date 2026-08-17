from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.supplier import Supplier
from modules.maintenance.domain.repositories.supplier_repository import SupplierRepository
from modules.maintenance.domain.value_objects.supplier_category import SupplierCategory
from modules.maintenance.domain.value_objects.supplier_status import SupplierStatus
from modules.maintenance.infrastructure.persistence.models.supplier_model import SupplierModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: SupplierModel) -> Supplier:
    return Supplier(
        id=model.id,
        codigo=model.codigo,
        razao_social=model.razao_social,
        cnpj=model.cnpj,
        telefone=model.telefone,
        category=SupplierCategory(model.tipo_principal) if model.tipo_principal else None,
        status=SupplierStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemySupplierRepository(SupplierRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Supplier | None:
        tenant_id = get_current_tenant_id()
        stmt = select(SupplierModel).where(
            SupplierModel.id == id, SupplierModel.tenant_id == tenant_id, SupplierModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_cnpj(self, cnpj: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(SupplierModel.id).where(SupplierModel.tenant_id == tenant_id, SupplierModel.cnpj == cnpj)
        if excluding_id is not None:
            stmt = stmt.where(SupplierModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        category: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Supplier], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(SupplierModel).where(SupplierModel.tenant_id == tenant_id, SupplierModel.excluido_em.is_(None))
        if status is not None:
            stmt = stmt.where(SupplierModel.status == status)
        if category is not None:
            stmt = stmt.where(SupplierModel.tipo_principal == category)
        if search is not None:
            stmt = stmt.where(SupplierModel.razao_social.ilike(f"%{search}%"))
        if created_from is not None:
            stmt = stmt.where(SupplierModel.criado_em >= created_from)
        if created_to is not None:
            stmt = stmt.where(SupplierModel.criado_em <= created_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SupplierModel.razao_social).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Supplier) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(SupplierModel, aggregate.id)
        if model is None:
            model = SupplierModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.razao_social = aggregate.razao_social
        model.cnpj = aggregate.cnpj
        model.telefone = aggregate.telefone
        model.tipo_principal = aggregate.category.value if aggregate.category else None
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Supplier]) -> list[Supplier]:
        raise NotImplementedError("Use list_page — filtros de Supplier são resolvidos via SQL")
