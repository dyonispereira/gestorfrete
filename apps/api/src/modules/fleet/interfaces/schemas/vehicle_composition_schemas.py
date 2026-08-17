from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.fleet.application.dtos.vehicle_composition_dto import VehicleCompositionDTO


class VehicleCompositionImplementResponse(BaseModel):
    implement_id: uuid.UUID
    order: int


class VehicleCompositionResponse(BaseModel):
    id: uuid.UUID
    tractor_unit_id: uuid.UUID
    combination_type: str
    total_axles: int
    status: str
    implements: list[VehicleCompositionImplementResponse]
    starts_at: datetime
    ends_at: datetime | None

    @staticmethod
    def from_dto(dto: VehicleCompositionDTO) -> "VehicleCompositionResponse":
        return VehicleCompositionResponse(
            id=dto.id,
            tractor_unit_id=dto.tractor_unit_id,
            combination_type=dto.combination_type,
            total_axles=dto.total_axles,
            status=dto.status,
            implements=[
                VehicleCompositionImplementResponse(implement_id=i.implement_id, order=i.order) for i in dto.implements
            ],
            starts_at=dto.starts_at,
            ends_at=dto.ends_at,
        )


class CreateVehicleCompositionImplementRequest(BaseModel):
    implement_id: uuid.UUID
    order: int = Field(ge=1)


class CreateVehicleCompositionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tractor_unit_id: uuid.UUID
    combination_type: str
    total_axles: int
    implements: list[CreateVehicleCompositionImplementRequest]
