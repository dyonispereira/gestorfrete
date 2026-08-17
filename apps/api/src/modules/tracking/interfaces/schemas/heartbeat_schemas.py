from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.tracking.application.dtos.heartbeat_dto import HeartbeatDTO


class HeartbeatResponse(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    external_protocol: str | None
    captured_at: datetime | None
    received_at: datetime
    processed_at: datetime

    @staticmethod
    def from_dto(dto: HeartbeatDTO) -> "HeartbeatResponse":
        return HeartbeatResponse(
            id=dto.id, equipment_id=dto.equipamento_rastreamento_id, external_protocol=dto.protocolo_externo,
            captured_at=dto.capturado_em, received_at=dto.recebido_em, processed_at=dto.processado_em,
        )
