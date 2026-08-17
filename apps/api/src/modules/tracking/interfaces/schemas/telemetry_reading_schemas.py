from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.tracking.application.dtos.telemetry_reading_dto import TelemetryReadingDTO


class TelemetryReadingResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    equipment_id: uuid.UUID
    position_id: uuid.UUID | None
    sensor_type: str
    value: str
    unit: str
    captured_at: datetime
    received_at: datetime
    processed_at: datetime

    @staticmethod
    def from_dto(dto: TelemetryReadingDTO) -> "TelemetryReadingResponse":
        return TelemetryReadingResponse(
            id=dto.id, vehicle_id=dto.veiculo_tracionador_id, equipment_id=dto.equipamento_rastreamento_id,
            position_id=dto.posicao_veiculo_id, sensor_type=dto.tipo_sensor, value=str(dto.valor), unit=dto.unidade,
            captured_at=dto.capturado_em, received_at=dto.recebido_em, processed_at=dto.processado_em,
        )
