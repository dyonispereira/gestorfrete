from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.tracking.domain.entities.location_origin import LocationOrigin


@dataclass(frozen=True)
class LocationOriginDTO:
    id: uuid.UUID
    nome: str
    precisao_tipica_metros: float | None

    @staticmethod
    def from_entity(entity: LocationOrigin) -> "LocationOriginDTO":
        return LocationOriginDTO(id=entity.id, nome=entity.nome, precisao_tipica_metros=entity.precisao_tipica_metros)
