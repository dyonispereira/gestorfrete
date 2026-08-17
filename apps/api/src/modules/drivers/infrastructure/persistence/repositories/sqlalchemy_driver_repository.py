from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.drivers.domain.entities.driver import Driver
from modules.drivers.domain.repositories.driver_repository import DriverRepository
from modules.drivers.domain.value_objects.employment_type import EmploymentType
from modules.drivers.domain.value_objects.fitness_status import FitnessStatus
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.identity_access.infrastructure.persistence.models.identity_models import UserModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: DriverModel) -> Driver:
    return Driver(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        cpf=model.cpf,
        telefone=model.telefone,
        email=model.email,
        employment_type=EmploymentType(model.tipo_vinculo),
        fitness_status=FitnessStatus(model.status_aptidao),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyDriverRepository(DriverRepository):
    """`get_by_user_id` importa `UserModel` de `identity_access` — leitura entre módulos via
    `infrastructure.persistence.models` (não `application`/`domain`) é aceita quando é só um
    `JOIN`/lookup de leitura, mesmo padrão já usado por `identity_access` para resolver `Session`→
    `Tenant` no Lote 2; nunca uma escrita cross-module."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Driver | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DriverModel).where(
            DriverModel.id == id, DriverModel.tenant_id == tenant_id, DriverModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_user_id(self, user_id: uuid.UUID) -> Driver | None:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(DriverModel)
            .join(UserModel, UserModel.motorista_id == DriverModel.id)
            .where(
                UserModel.id == user_id,
                DriverModel.tenant_id == tenant_id,
                DriverModel.excluido_em.is_(None),
            )
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_by_cpf_across_tenants(self, cpf: str) -> list[tuple[Driver, uuid.UUID]]:
        # D408 — mesma exceção documentada de `UserRepository.get_by_email`: sem filtro de tenant,
        # só usado pelo login Mobile antes de qualquer `set_current_tenant_id` ocorrer.
        stmt = select(DriverModel).where(DriverModel.cpf == cpf, DriverModel.excluido_em.is_(None))
        models = (await self._session.execute(stmt)).scalars().all()
        return [(_to_entity(m), m.tenant_id) for m in models]

    async def exists_with_cpf(self, cpf: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(DriverModel.id).where(DriverModel.tenant_id == tenant_id, DriverModel.cpf == cpf)
        if excluding_id is not None:
            stmt = stmt.where(DriverModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        employment_type: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Driver], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(DriverModel).where(DriverModel.tenant_id == tenant_id, DriverModel.excluido_em.is_(None))
        if status is not None:
            stmt = stmt.where(DriverModel.status_aptidao == status)
        if employment_type is not None:
            stmt = stmt.where(DriverModel.tipo_vinculo == employment_type)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(DriverModel.nome.ilike(like) | DriverModel.cpf.ilike(like))
        if created_from is not None:
            stmt = stmt.where(DriverModel.criado_em >= created_from)
        if created_to is not None:
            stmt = stmt.where(DriverModel.criado_em <= created_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(DriverModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Driver) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(DriverModel, aggregate.id)
        if model is None:
            model = DriverModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.nome = aggregate.nome
        model.cpf = aggregate.cpf
        model.telefone = aggregate.telefone
        model.email = aggregate.email
        model.tipo_vinculo = aggregate.employment_type.value
        model.status_aptidao = aggregate.fitness_status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Driver]) -> list[Driver]:
        raise NotImplementedError("Use list_page — filtros de Driver são resolvidos via SQL")
