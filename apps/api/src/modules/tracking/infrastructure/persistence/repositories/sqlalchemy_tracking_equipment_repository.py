from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.tracking_equipment import TrackingEquipment
from modules.tracking.domain.repositories.tracking_equipment_repository import TrackingEquipmentRepository
from modules.tracking.domain.value_objects.equipment_status import EquipmentStatus
from modules.tracking.domain.value_objects.equipment_type import EquipmentType
from modules.tracking.infrastructure.persistence.models.tracking_equipment_model import TrackingEquipmentModel


def _to_entity(model: TrackingEquipmentModel) -> TrackingEquipment:
    return TrackingEquipment(
        id=model.id, provedor_rastreamento_id=model.provedor_rastreamento_id,
        identificador_serial=model.identificador_serial, tipo_equipamento=EquipmentType(model.tipo_equipamento),
        veiculo_tracionador_id=model.veiculo_tracionador_id, data_inicio_vigencia=model.data_inicio_vigencia,
        data_fim_vigencia=model.data_fim_vigencia, alterado_por=model.alterado_por,
        status=EquipmentStatus(model.status),
    )


class SqlAlchemyTrackingEquipmentRepository(TrackingEquipmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> TrackingEquipment | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEquipmentModel).where(
            TrackingEquipmentModel.id == id, TrackingEquipmentModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_serial(self, identificador_serial: str) -> TrackingEquipment | None:
        # Único globalmente (D084) — sem filtro de tenant, dado físico do equipamento.
        stmt = select(TrackingEquipmentModel).where(
            TrackingEquipmentModel.identificador_serial == identificador_serial
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_principal_vigente(self, veiculo_tracionador_id: uuid.UUID) -> TrackingEquipment | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEquipmentModel).where(
            TrackingEquipmentModel.tenant_id == tenant_id,
            TrackingEquipmentModel.veiculo_tracionador_id == veiculo_tracionador_id,
            TrackingEquipmentModel.tipo_equipamento == EquipmentType.PRINCIPAL.value,
            TrackingEquipmentModel.data_fim_vigencia.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, vehicle_id: uuid.UUID | None, provider_id: uuid.UUID | None,
        equipment_type: str | None, status: str | None,
    ) -> tuple[list[TrackingEquipment], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEquipmentModel).where(TrackingEquipmentModel.tenant_id == tenant_id)
        if vehicle_id is not None:
            stmt = stmt.where(TrackingEquipmentModel.veiculo_tracionador_id == vehicle_id)
        if provider_id is not None:
            stmt = stmt.where(TrackingEquipmentModel.provedor_rastreamento_id == provider_id)
        if equipment_type is not None:
            stmt = stmt.where(TrackingEquipmentModel.tipo_equipamento == equipment_type)
        if status is not None:
            stmt = stmt.where(TrackingEquipmentModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(TrackingEquipmentModel.identificador_serial.asc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, equipment: TrackingEquipment) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(TrackingEquipmentModel, equipment.id)
        if model is None:
            model = TrackingEquipmentModel(id=equipment.id, tenant_id=tenant_id)
            self._session.add(model)
        model.provedor_rastreamento_id = equipment.provedor_rastreamento_id
        model.identificador_serial = equipment.identificador_serial
        model.tipo_equipamento = equipment.tipo_equipamento.value
        model.veiculo_tracionador_id = equipment.veiculo_tracionador_id
        model.data_inicio_vigencia = equipment.data_inicio_vigencia
        model.data_fim_vigencia = equipment.data_fim_vigencia
        model.alterado_por = equipment.alterado_por
        model.status = equipment.status.value
        await self._session.flush()
