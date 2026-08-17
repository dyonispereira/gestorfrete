from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.identity_access.domain.entities.employee import Employee
from modules.identity_access.domain.repositories.employee_repository import EmployeeRepository
from modules.identity_access.domain.value_objects.employee_status import EmployeeStatus
from modules.identity_access.infrastructure.persistence.models.identity_models import EmployeeModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: EmployeeModel) -> Employee:
    return Employee(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        cargo=model.cargo,
        data_admissao=model.data_admissao,
        status=EmployeeStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyEmployeeRepository(EmployeeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Employee | None:
        tenant_id = get_current_tenant_id()
        stmt = select(EmployeeModel).where(
            EmployeeModel.id == id, EmployeeModel.tenant_id == tenant_id, EmployeeModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Employee], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(EmployeeModel).where(EmployeeModel.tenant_id == tenant_id, EmployeeModel.excluido_em.is_(None))
        if status is not None:
            stmt = stmt.where(EmployeeModel.status == status)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(EmployeeModel.nome.ilike(like) | EmployeeModel.cargo.ilike(like))
        if created_from is not None:
            stmt = stmt.where(EmployeeModel.criado_em >= created_from)
        if created_to is not None:
            stmt = stmt.where(EmployeeModel.criado_em <= created_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(EmployeeModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Employee) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(EmployeeModel, aggregate.id)
        if model is None:
            model = EmployeeModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.nome = aggregate.nome
        model.cargo = aggregate.cargo
        model.data_admissao = aggregate.data_admissao
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Employee]) -> list[Employee]:
        raise NotImplementedError("Use list_page — filtros de Employee são resolvidos via SQL")
