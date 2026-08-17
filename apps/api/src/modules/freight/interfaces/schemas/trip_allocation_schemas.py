from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.trip_allocation_dto import TripAllocationDTO


class TripAllocationResponse(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    implement_id: uuid.UUID | None
    status: str
    replacement_reason: str | None
    created_at: datetime

    @staticmethod
    def from_dto(dto: TripAllocationDTO) -> "TripAllocationResponse":
        return TripAllocationResponse(
            id=dto.id, driver_id=dto.motorista_id, tractor_unit_id=dto.veiculo_tracionador_id,
            implement_id=dto.implemento_id, status=dto.status, replacement_reason=dto.motivo_troca,
            created_at=dto.criado_em,
        )


class CreateTripAllocationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    driver_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    implement_id: uuid.UUID | None = None


class ReallocateTripResourcesRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    driver_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    implement_id: uuid.UUID | None = None
    reason: str
