from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.fleet.domain.entities.odometer_reading import OdometerReading


@dataclass(frozen=True)
class OdometerReadingDTO:
    id: uuid.UUID
    value_km: Decimal
    origin: str
    trip_id: uuid.UUID | None
    captured_at: datetime

    @staticmethod
    def from_entity(reading: OdometerReading) -> "OdometerReadingDTO":
        return OdometerReadingDTO(
            id=reading.id, value_km=reading.valor_km, origin=reading.origem.value, trip_id=reading.viagem_id,
            captured_at=reading.data_hora,
        )
