from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.fleet.application.dtos.vehicle_availability_dto import VehicleAvailabilityDTO


class VehicleAvailabilityResponse(BaseModel):
    """D247 — todo campo `readOnly` no contrato; este schema nunca aparece como corpo de
    request em nenhum router (`AVAILABILITY_IMPLEMENTATION.md`)."""

    vehicle_id: uuid.UUID
    status: str
    current_driver_id: uuid.UUID | None
    current_implement_id: uuid.UUID | None
    updated_at: datetime

    @staticmethod
    def from_dto(dto: VehicleAvailabilityDTO) -> "VehicleAvailabilityResponse":
        return VehicleAvailabilityResponse(
            vehicle_id=dto.vehicle_id, status=dto.status, current_driver_id=dto.current_driver_id,
            current_implement_id=dto.current_implement_id, updated_at=dto.updated_at,
        )
