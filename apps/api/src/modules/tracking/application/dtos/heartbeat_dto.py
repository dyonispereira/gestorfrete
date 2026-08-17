from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tracking.domain.entities.heartbeat import Heartbeat


@dataclass(frozen=True)
class HeartbeatDTO:
    id: uuid.UUID
    equipamento_rastreamento_id: uuid.UUID
    protocolo_externo: str | None
    capturado_em: datetime | None
    recebido_em: datetime
    processado_em: datetime

    @staticmethod
    def from_entity(entity: Heartbeat) -> "HeartbeatDTO":
        return HeartbeatDTO(
            id=entity.id, equipamento_rastreamento_id=entity.equipamento_rastreamento_id,
            protocolo_externo=entity.protocolo_externo, capturado_em=entity.capturado_em,
            recebido_em=entity.recebido_em, processado_em=entity.processado_em,
        )
