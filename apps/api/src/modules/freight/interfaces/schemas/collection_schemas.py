from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.collection_dto import CollectionDTO


class CollectionResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    registered_at: datetime
    cargo_checked: bool
    trip_operational_status: str

    @staticmethod
    def from_dto(dto: CollectionDTO) -> "CollectionResponse":
        return CollectionResponse(
            id=dto.id, trip_id=dto.viagem_id, registered_at=dto.data_hora, cargo_checked=dto.conferencia_ok,
            trip_operational_status=dto.trip_status_operacional,
        )


class RegisterCollectionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cargo_checked: bool = False
