from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO


class OccurrenceResponse(BaseModel):
    id: uuid.UUID
    type: str
    description: str
    severity: str | None
    status: str
    occurred_at: datetime

    @staticmethod
    def from_dto(dto: OccurrenceDTO) -> "OccurrenceResponse":
        return OccurrenceResponse(
            id=dto.id, type=dto.tipo, description=dto.descricao, severity=dto.gravidade, status=dto.status,
            occurred_at=dto.data_hora,
        )


class OccurrenceLocationPayload(BaseModel):
    latitude: float
    longitude: float


class CreateOccurrenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    description: str
    severity: str | None = None
    occurred_at: datetime
    location: OccurrenceLocationPayload | None = None


class UpdateOccurrenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str | None = None
    severity: str | None = None
    status: str | None = None
