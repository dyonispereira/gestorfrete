from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.tracking.application.dtos.tracking_equipment_dto import TrackingEquipmentDTO


class TrackingEquipmentResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    serial_identifier: str
    equipment_type: str
    vehicle_id: uuid.UUID | None
    starts_at: datetime | None
    ends_at: datetime | None
    status: str

    @staticmethod
    def from_dto(dto: TrackingEquipmentDTO) -> "TrackingEquipmentResponse":
        return TrackingEquipmentResponse(
            id=dto.id, provider_id=dto.provedor_rastreamento_id, serial_identifier=dto.identificador_serial,
            equipment_type=dto.tipo_equipamento, vehicle_id=dto.veiculo_tracionador_id,
            starts_at=dto.data_inicio_vigencia, ends_at=dto.data_fim_vigencia, status=dto.status,
        )


class CreateTrackingEquipmentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider_id: uuid.UUID
    serial_identifier: str
    equipment_type: str
    vehicle_id: uuid.UUID | None = None


class UpdateTrackingEquipmentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vehicle_id: uuid.UUID | None = None
    ends_at: datetime | None = None
    status: str | None = None
