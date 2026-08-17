from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle import Vehicle
from modules.fleet.domain.repositories.vehicle_repository import VehicleRepository
from modules.fleet.domain.value_objects.vehicle_status import VehicleStatus
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: VehicleModel) -> Vehicle:
    return Vehicle(
        id=model.id,
        codigo=model.codigo,
        placa=model.placa,
        renavam=model.renavam,
        fabricante=model.fabricante,
        modelo=model.modelo,
        ano_fabricacao=model.ano_fabricacao,
        categoria_veiculo_id=model.categoria_veiculo_id,
        filial_id=model.filial_id,
        status=VehicleStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyVehicleRepository(VehicleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Vehicle | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleModel).where(
            VehicleModel.id == id, VehicleModel.tenant_id == tenant_id, VehicleModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_placa_and_tenant(self, placa: str, tenant_id: uuid.UUID) -> Vehicle | None:
        # D408 — tenant explícito no parâmetro, nunca `get_current_tenant_id()`: chamado pelo login
        # Mobile para validar um candidato antes de qualquer contexto de tenant existir.
        stmt = select(VehicleModel).where(
            VehicleModel.placa == placa, VehicleModel.tenant_id == tenant_id, VehicleModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_placa(self, placa: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleModel.id).where(VehicleModel.tenant_id == tenant_id, VehicleModel.placa == placa)
        if excluding_id is not None:
            stmt = stmt.where(VehicleModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def exists_with_renavam(self, renavam: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleModel.id).where(VehicleModel.tenant_id == tenant_id, VehicleModel.renavam == renavam)
        if excluding_id is not None:
            stmt = stmt.where(VehicleModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        search: str | None,
        placa: str | None,
        status: str | None,
        categoria_id: uuid.UUID | None,
        fabricante: str | None,
        modelo: str | None,
        ano: int | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Vehicle], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleModel).where(VehicleModel.tenant_id == tenant_id, VehicleModel.excluido_em.is_(None))
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(VehicleModel.placa.ilike(like) | VehicleModel.fabricante.ilike(like) | VehicleModel.modelo.ilike(like))
        if placa is not None:
            stmt = stmt.where(VehicleModel.placa == placa)
        if status is not None:
            stmt = stmt.where(VehicleModel.status == status)
        if categoria_id is not None:
            stmt = stmt.where(VehicleModel.categoria_veiculo_id == categoria_id)
        if fabricante is not None:
            stmt = stmt.where(VehicleModel.fabricante == fabricante)
        if modelo is not None:
            stmt = stmt.where(VehicleModel.modelo == modelo)
        if ano is not None:
            stmt = stmt.where(VehicleModel.ano_fabricacao == ano)
        if created_from is not None:
            stmt = stmt.where(VehicleModel.criado_em >= created_from)
        if created_to is not None:
            stmt = stmt.where(VehicleModel.criado_em <= created_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleModel.placa).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Vehicle) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleModel, aggregate.id)
        if model is None:
            model = VehicleModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.placa = aggregate.placa
        model.renavam = aggregate.renavam
        model.fabricante = aggregate.fabricante
        model.modelo = aggregate.modelo
        model.ano_fabricacao = aggregate.ano_fabricacao
        model.categoria_veiculo_id = aggregate.categoria_veiculo_id
        model.filial_id = aggregate.filial_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Vehicle]) -> list[Vehicle]:
        raise NotImplementedError("Use list_page — filtros de Vehicle são resolvidos via SQL")
