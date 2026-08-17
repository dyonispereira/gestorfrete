from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.tracking.application.dtos.tracking_event_dto import TrackingEventDTO


class TrackingEventResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    type: str
    position_id: uuid.UUID | None
    geofence_id: uuid.UUID | None
    speed_limit_config_id: uuid.UUID | None
    detected_value: str | None
    severity: str
    occurred_at: datetime

    @staticmethod
    def from_dto(dto: TrackingEventDTO) -> "TrackingEventResponse":
        return TrackingEventResponse(
            id=dto.id, vehicle_id=dto.veiculo_tracionador_id, type=dto.tipo, position_id=dto.posicao_veiculo_id,
            geofence_id=dto.cerca_eletronica_id, speed_limit_config_id=dto.configuracao_limite_velocidade_id,
            detected_value=str(dto.valor_detectado) if dto.valor_detectado is not None else None,
            severity=dto.severidade, occurred_at=dto.data_hora,
        )
