from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_availability import VehicleAvailability
from modules.fleet.domain.repositories.vehicle_availability_repository import VehicleAvailabilityRepository
from modules.fleet.domain.value_objects.availability_status import AvailabilityStatus
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel


def _to_entity(model: VehicleAvailabilityModel) -> VehicleAvailability:
    return VehicleAvailability(
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        status=AvailabilityStatus(model.status),
        motorista_atual_id=model.motorista_atual_id,
        implemento_atual_id=model.implemento_atual_id,
        atualizado_em=model.atualizado_em,
    )


class SqlAlchemyVehicleAvailabilityRepository(VehicleAvailabilityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_vehicle_id(self, veiculo_tracionador_id: uuid.UUID) -> VehicleAvailability | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleAvailabilityModel).where(
            VehicleAvailabilityModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleAvailabilityModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(self, *, page: int, limit: int, status: str | None) -> tuple[list[VehicleAvailability], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(VehicleAvailabilityModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleAvailabilityModel.atualizado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def apply(
        self,
        *,
        veiculo_tracionador_id: uuid.UUID,
        status: AvailabilityStatus,
        motorista_atual_id: uuid.UUID | None,
        implemento_atual_id: uuid.UUID | None,
        now: datetime,
    ) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleAvailabilityModel, veiculo_tracionador_id)
        if model is None:
            model = VehicleAvailabilityModel(veiculo_tracionador_id=veiculo_tracionador_id, tenant_id=tenant_id)
            self._session.add(model)
        model.status = status.value
        model.motorista_atual_id = motorista_atual_id
        model.implemento_atual_id = implemento_atual_id
        model.atualizado_em = now
        await self._session.flush()
