from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.tracking.domain.entities.geofence import Geofence


@dataclass(frozen=True)
class GeoPointDTO:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class GeofenceDTO:
    id: uuid.UUID
    nome: str
    tipo_geometria: str
    centro: GeoPointDTO | None
    raio_metros: float | None
    poligono: list[GeoPointDTO] | None
    cliente_id: uuid.UUID | None
    filial_id: uuid.UUID | None
    status: str

    @staticmethod
    def from_entity(entity: Geofence) -> "GeofenceDTO":
        return GeofenceDTO(
            id=entity.id, nome=entity.nome, tipo_geometria=entity.tipo_geometria.value,
            centro=GeoPointDTO(latitude=entity.centro.latitude, longitude=entity.centro.longitude)
            if entity.centro is not None else None,
            raio_metros=entity.raio_metros,
            poligono=[GeoPointDTO(latitude=p.latitude, longitude=p.longitude) for p in entity.poligono]
            if entity.poligono is not None else None,
            cliente_id=entity.cliente_id, filial_id=entity.filial_id, status=entity.status.value,
        )
