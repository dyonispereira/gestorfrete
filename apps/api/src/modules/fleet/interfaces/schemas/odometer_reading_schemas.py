from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.fleet.application.dtos.odometer_reading_dto import OdometerReadingDTO


class OdometerReadingResponse(BaseModel):
    id: uuid.UUID
    value_km: Decimal
    origin: str
    trip_id: uuid.UUID | None
    captured_at: datetime

    @staticmethod
    def from_dto(dto: OdometerReadingDTO) -> "OdometerReadingResponse":
        return OdometerReadingResponse(
            id=dto.id, value_km=dto.value_km, origin=dto.origin, trip_id=dto.trip_id, captured_at=dto.captured_at
        )


class CreateOdometerReadingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value_km: Decimal
    origin: str
    trip_id: uuid.UUID | None = None
