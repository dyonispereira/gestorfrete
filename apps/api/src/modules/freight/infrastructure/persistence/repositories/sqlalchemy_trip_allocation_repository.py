from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.trip_allocation import TripAllocation
from modules.freight.domain.repositories.trip_allocation_repository import TripAllocationRepository
from modules.freight.domain.value_objects.allocation_status import AllocationStatus
from modules.freight.infrastructure.persistence.models.trip_allocation_model import TripAllocationModel


def _to_entity(model: TripAllocationModel) -> TripAllocation:
    return TripAllocation(
        id=model.id,
        viagem_id=model.viagem_id,
        motorista_id=model.motorista_id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        implemento_id=model.implemento_id,
        status=AllocationStatus(model.status),
        motivo_troca=model.motivo_troca,
        criado_em=model.criado_em,
        criado_por=model.criado_por,
    )


class SqlAlchemyTripAllocationRepository(TripAllocationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_for_trip(self, viagem_id: uuid.UUID) -> TripAllocation | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TripAllocationModel).where(
            TripAllocationModel.tenant_id == tenant_id,
            TripAllocationModel.viagem_id == viagem_id,
            TripAllocationModel.status == AllocationStatus.VIGENTE.value,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_trip(self, viagem_id: uuid.UUID, *, include_superseded: bool) -> list[TripAllocation]:
        tenant_id = get_current_tenant_id()
        stmt = select(TripAllocationModel).where(
            TripAllocationModel.tenant_id == tenant_id, TripAllocationModel.viagem_id == viagem_id
        )
        if not include_superseded:
            stmt = stmt.where(TripAllocationModel.status == AllocationStatus.VIGENTE.value)
        stmt = stmt.order_by(TripAllocationModel.criado_em.desc())
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def exists_vigente_for_vehicle_excluding_trip(
        self, veiculo_tracionador_id: uuid.UUID, viagem_id: uuid.UUID
    ) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(TripAllocationModel.id).where(
            TripAllocationModel.tenant_id == tenant_id,
            TripAllocationModel.veiculo_tracionador_id == veiculo_tracionador_id,
            TripAllocationModel.status == AllocationStatus.VIGENTE.value,
            TripAllocationModel.viagem_id != viagem_id,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def add(self, allocation: TripAllocation) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(TripAllocationModel, allocation.id)
        if model is None:
            model = TripAllocationModel(id=allocation.id, tenant_id=tenant_id, viagem_id=allocation.viagem_id)
            self._session.add(model)
        model.motorista_id = allocation.motorista_id
        model.veiculo_tracionador_id = allocation.veiculo_tracionador_id
        model.implemento_id = allocation.implemento_id
        model.status = allocation.status.value
        model.motivo_troca = allocation.motivo_troca
        model.criado_em = allocation.criado_em
        model.criado_por = allocation.criado_por
        await self._session.flush()
