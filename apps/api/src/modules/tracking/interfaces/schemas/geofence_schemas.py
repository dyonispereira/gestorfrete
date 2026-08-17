from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.tracking.application.dtos.geofence_dto import GeofenceDTO
from modules.tracking.application.dtos.speed_limit_config_dto import SpeedLimitConfigDTO
from modules.tracking.interfaces.schemas.geo_point_schema import GeoPointSchema


class GeofenceResponse(BaseModel):
    id: uuid.UUID
    name: str
    geometry_type: str
    center: GeoPointSchema | None
    radius_meters: float | None
    polygon: list[GeoPointSchema] | None
    client_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    status: str

    @staticmethod
    def from_dto(dto: GeofenceDTO) -> "GeofenceResponse":
        return GeofenceResponse(
            id=dto.id, name=dto.nome, geometry_type=dto.tipo_geometria,
            center=GeoPointSchema(latitude=dto.centro.latitude, longitude=dto.centro.longitude)
            if dto.centro is not None else None,
            radius_meters=dto.raio_metros,
            polygon=[GeoPointSchema(latitude=p.latitude, longitude=p.longitude) for p in dto.poligono]
            if dto.poligono is not None else None,
            client_id=dto.cliente_id, branch_id=dto.filial_id, status=dto.status,
        )


class CreateGeofenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    geometry_type: str
    center: GeoPointSchema | None = None
    radius_meters: float | None = None
    polygon: list[GeoPointSchema] | None = None
    client_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class UpdateGeofenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    geometry_type: str | None = None
    center: GeoPointSchema | None = None
    radius_meters: float | None = None
    polygon: list[GeoPointSchema] | None = None
    client_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    status: str | None = None


class SpeedLimitConfigResponse(BaseModel):
    id: uuid.UUID
    vehicle_category_id: uuid.UUID | None
    limit_kmh: str
    status: str

    @staticmethod
    def from_dto(dto: SpeedLimitConfigDTO) -> "SpeedLimitConfigResponse":
        return SpeedLimitConfigResponse(
            id=dto.id, vehicle_category_id=dto.categoria_veiculo_id, limit_kmh=str(dto.limite_kmh),
            status=dto.status,
        )


class CreateSpeedLimitConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vehicle_category_id: uuid.UUID | None = None
    limit_kmh: str


class UpdateSpeedLimitConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    limit_kmh: str | None = None
    status: str | None = None
