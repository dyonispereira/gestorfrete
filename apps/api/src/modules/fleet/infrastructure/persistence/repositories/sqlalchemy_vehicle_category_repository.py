from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_category import VehicleCategory
from modules.fleet.domain.repositories.vehicle_category_repository import VehicleCategoryRepository
from modules.fleet.domain.value_objects.vehicle_category_status import VehicleCategoryStatus
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel


def _to_entity(model: VehicleCategoryModel) -> VehicleCategory:
    return VehicleCategory(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        status=VehicleCategoryStatus(model.status),
        created_at=model.criado_em,
        updated_at=model.atualizado_em,
    )


class SqlAlchemyVehicleCategoryRepository(VehicleCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> VehicleCategory | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCategoryModel).where(
            VehicleCategoryModel.id == id, VehicleCategoryModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, category: VehicleCategory) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleCategoryModel, category.id)
        if model is None:
            model = VehicleCategoryModel(id=category.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = category.codigo
        model.nome = category.nome
        model.status = category.status.value
        model.criado_em = category.created_at
        model.atualizado_em = category.updated_at
        await self._session.flush()

    async def exists_with_nome(self, nome: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCategoryModel.id).where(
            VehicleCategoryModel.tenant_id == tenant_id, VehicleCategoryModel.nome == nome
        )
        if excluding_id is not None:
            stmt = stmt.where(VehicleCategoryModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, status: str | None, search: str | None
    ) -> tuple[list[VehicleCategory], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(VehicleCategoryModel.status == status)
        if search is not None:
            stmt = stmt.where(VehicleCategoryModel.nome.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleCategoryModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total
