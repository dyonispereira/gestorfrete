from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.tracking.application.dtos.vehicle_position_dto import VehiclePositionDTO
from modules.tracking.interfaces.schemas.geo_point_schema import GeoPointSchema


class VehiclePositionResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    equipment_id: uuid.UUID
    location: GeoPointSchema
    origin_id: uuid.UUID
    precision_meters: float | None
    satellite_count: int | None
    hdop: float | None
    confidence_level: float | None
    captured_at: datetime
    received_at: datetime
    processed_at: datetime

    @staticmethod
    def from_dto(dto: VehiclePositionDTO) -> "VehiclePositionResponse":
        return VehiclePositionResponse(
            id=dto.id, vehicle_id=dto.veiculo_tracionador_id, equipment_id=dto.equipamento_rastreamento_id,
            location=GeoPointSchema(latitude=dto.latitude, longitude=dto.longitude),
            origin_id=dto.origem_localizacao_id, precision_meters=dto.precisao_metros,
            satellite_count=dto.numero_satelites, hdop=dto.hdop, confidence_level=dto.nivel_confianca,
            captured_at=dto.capturado_em, received_at=dto.recebido_em, processed_at=dto.processado_em,
        )
