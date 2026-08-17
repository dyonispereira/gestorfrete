from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_technical_sheet import VehicleTechnicalSheet
from modules.fleet.domain.repositories.vehicle_technical_sheet_repository import VehicleTechnicalSheetRepository
from modules.fleet.domain.value_objects.fuel_type import FuelType
from modules.fleet.infrastructure.persistence.models.vehicle_technical_sheet_model import (
    VehicleTechnicalSheetModel,
)


def _to_entity(model: VehicleTechnicalSheetModel) -> VehicleTechnicalSheet:
    return VehicleTechnicalSheet(
        id=model.id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        chassi=model.chassi,
        motor=model.motor,
        eixos=model.eixos,
        tara=model.tara,
        capacidade_carga=model.capacidade_carga,
        pbt=model.pbt,
        rntrc_proprietario=model.rntrc_proprietario,
        combustivel=FuelType(model.combustivel),
    )


class SqlAlchemyVehicleTechnicalSheetRepository(VehicleTechnicalSheetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_vehicle_id(self, veiculo_tracionador_id: uuid.UUID) -> VehicleTechnicalSheet | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleTechnicalSheetModel).where(
            VehicleTechnicalSheetModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleTechnicalSheetModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_chassi(self, chassi: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        # `chassi` é único na plataforma inteira, não só por tenant (D082/DDL confirma:
        # `uq_fichas_tecnicas_veiculo_chassi` sem `tenant_id`) — única checagem deste projeto que
        # deliberadamente não filtra por tenant.
        stmt = select(VehicleTechnicalSheetModel.id).where(VehicleTechnicalSheetModel.chassi == chassi)
        if excluding_id is not None:
            stmt = stmt.where(VehicleTechnicalSheetModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def add(self, sheet: VehicleTechnicalSheet) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleTechnicalSheetModel, sheet.id)
        if model is None:
            model = VehicleTechnicalSheetModel(
                id=sheet.id, tenant_id=tenant_id, veiculo_tracionador_id=sheet.veiculo_tracionador_id
            )
            self._session.add(model)
        model.chassi = sheet.chassi
        model.motor = sheet.motor
        model.eixos = sheet.eixos
        model.tara = sheet.tara
        model.capacidade_carga = sheet.capacidade_carga
        model.pbt = sheet.pbt
        model.rntrc_proprietario = sheet.rntrc_proprietario
        model.combustivel = sheet.combustivel.value
        await self._session.flush()
