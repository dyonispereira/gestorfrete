from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.cost_center import CostCenter
from modules.financial.domain.repositories.cost_center_repository import CostCenterRepository
from modules.financial.domain.value_objects.cost_center_status import CostCenterStatus
from modules.financial.infrastructure.persistence.models.cost_center_model import CostCenterModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: CostCenterModel) -> CostCenter:
    return CostCenter(
        id=model.id,
        codigo=model.codigo,
        codigo_contabil=model.codigo_contabil,
        nome=model.nome,
        filial_id=model.filial_id,
        status=CostCenterStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyCostCenterRepository(CostCenterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> CostCenter | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CostCenterModel).where(
            CostCenterModel.id == id, CostCenterModel.tenant_id == tenant_id, CostCenterModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_codigo_contabil(self, codigo_contabil: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(CostCenterModel.id).where(
            CostCenterModel.tenant_id == tenant_id, CostCenterModel.codigo_contabil == codigo_contabil
        )
        if excluding_id is not None:
            stmt = stmt.where(CostCenterModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, status: str | None, branch_id: uuid.UUID | None, search: str | None
    ) -> tuple[list[CostCenter], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(CostCenterModel).where(
            CostCenterModel.tenant_id == tenant_id, CostCenterModel.excluido_em.is_(None)
        )
        if status is not None:
            stmt = stmt.where(CostCenterModel.status == status)
        if branch_id is not None:
            stmt = stmt.where(CostCenterModel.filial_id == branch_id)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(CostCenterModel.nome.ilike(like) | CostCenterModel.codigo_contabil.ilike(like))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(CostCenterModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: CostCenter) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(CostCenterModel, aggregate.id)
        if model is None:
            model = CostCenterModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.codigo_contabil = aggregate.codigo_contabil
        model.nome = aggregate.nome
        model.filial_id = aggregate.filial_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[CostCenter]) -> list[CostCenter]:
        raise NotImplementedError("Use list_page — filtros de CostCenter são resolvidos via SQL")
