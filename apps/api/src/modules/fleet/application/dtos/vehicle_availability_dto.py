from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.entities.vehicle_availability import VehicleAvailability


@dataclass(frozen=True)
class VehicleAvailabilityDTO:
    vehicle_id: uuid.UUID
    status: str
    current_driver_id: uuid.UUID | None
    current_implement_id: uuid.UUID | None
    updated_at: datetime

    @staticmethod
    def from_entity(availability: VehicleAvailability) -> "VehicleAvailabilityDTO":
        return VehicleAvailabilityDTO(
            vehicle_id=availability.veiculo_tracionador_id,
            status=availability.status.value,
            current_driver_id=availability.motorista_atual_id,
            current_implement_id=availability.implemento_atual_id,
            updated_at=availability.atualizado_em,
        )
