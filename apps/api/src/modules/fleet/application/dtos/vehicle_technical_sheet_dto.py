from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.fleet.domain.entities.vehicle_technical_sheet import VehicleTechnicalSheet


@dataclass(frozen=True)
class VehicleTechnicalSheetDTO:
    id: uuid.UUID
    manufacturer: str
    model: str
    manufacture_year: int
    category_id: uuid.UUID
    chassis: str
    engine: str | None
    axles: int
    tare_weight: Decimal
    load_capacity: Decimal
    gross_vehicle_weight: Decimal
    owner_rntrc: str | None
    fuel_type: str

    @staticmethod
    def from_entity_and_vehicle(sheet: VehicleTechnicalSheet, *, manufacturer: str, model: str, manufacture_year: int, category_id: uuid.UUID) -> "VehicleTechnicalSheetDTO":
        return VehicleTechnicalSheetDTO(
            id=sheet.id,
            manufacturer=manufacturer,
            model=model,
            manufacture_year=manufacture_year,
            category_id=category_id,
            chassis=sheet.chassi,
            engine=sheet.motor,
            axles=sheet.eixos,
            tare_weight=sheet.tara,
            load_capacity=sheet.capacidade_carga,
            gross_vehicle_weight=sheet.pbt,
            owner_rntrc=sheet.rntrc_proprietario,
            fuel_type=sheet.combustivel.value,
        )
