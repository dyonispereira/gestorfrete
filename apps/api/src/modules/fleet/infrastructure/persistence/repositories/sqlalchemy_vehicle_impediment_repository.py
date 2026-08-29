from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_impediment import VehicleImpediment
from modules.fleet.domain.repositories.vehicle_impediment_repository import VehicleImpedimentRepository
from modules.fleet.domain.value_objects.impediment_type import ImpedimentoTipo
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel


def _to_entity(model: VehicleImpedimentModel) -> VehicleImpediment:
    return VehicleImpediment(
        id=model.id, veiculo_tracionador_id=model.veiculo_tracionador_id, tipo=ImpedimentoTipo(model.tipo),
        referencia_id=model.referencia_id, motorista_id=model.motorista_id, implemento_id=model.implemento_id,
        iniciado_em=model.iniciado_em, encerrado_em=model.encerrado_em,
    )


class SqlAlchemyVehicleImpedimentRepository(VehicleImpedimentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(
        self, *, veiculo_tracionador_id: uuid.UUID, tipo: ImpedimentoTipo, referencia_id: uuid.UUID
    ) -> VehicleImpediment | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleImpedimentModel).where(
            VehicleImpedimentModel.tenant_id == tenant_id,
            VehicleImpedimentModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleImpedimentModel.tipo == tipo.value,
            VehicleImpedimentModel.referencia_id == referencia_id,
            VehicleImpedimentModel.encerrado_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_active(self, veiculo_tracionador_id: uuid.UUID) -> list[VehicleImpediment]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleImpedimentModel).where(
            VehicleImpedimentModel.tenant_id == tenant_id,
            VehicleImpedimentModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleImpedimentModel.encerrado_em.is_(None),
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, impediment: VehicleImpediment) -> None:
        tenant_id = get_current_tenant_id()
        model = VehicleImpedimentModel(
            id=impediment.id, tenant_id=tenant_id, veiculo_tracionador_id=impediment.veiculo_tracionador_id,
            tipo=impediment.tipo.value, referencia_id=impediment.referencia_id,
            motorista_id=impediment.motorista_id, implemento_id=impediment.implemento_id,
            iniciado_em=impediment.iniciado_em, encerrado_em=impediment.encerrado_em,
        )
        self._session.add(model)
        await self._session.flush()

    async def close(
        self, *, veiculo_tracionador_id: uuid.UUID, tipo: ImpedimentoTipo, referencia_id: uuid.UUID, now: datetime
    ) -> None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleImpedimentModel).where(
            VehicleImpedimentModel.tenant_id == tenant_id,
            VehicleImpedimentModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleImpedimentModel.tipo == tipo.value,
            VehicleImpedimentModel.referencia_id == referencia_id,
            VehicleImpedimentModel.encerrado_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return
        model.encerrado_em = now
        await self._session.flush()
