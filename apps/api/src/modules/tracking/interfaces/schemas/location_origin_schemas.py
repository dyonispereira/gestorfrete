from __future__ import annotations

import uuid

from pydantic import BaseModel

from modules.tracking.application.dtos.location_origin_dto import LocationOriginDTO


class LocationOriginResponse(BaseModel):
    id: uuid.UUID
    name: str
    typical_precision_meters: float | None

    @staticmethod
    def from_dto(dto: LocationOriginDTO) -> "LocationOriginResponse":
        return LocationOriginResponse(id=dto.id, name=dto.nome, typical_precision_meters=dto.precisao_tipica_metros)
