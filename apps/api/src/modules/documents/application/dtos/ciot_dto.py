from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.documents.domain.entities.ciot import Ciot


@dataclass(frozen=True)
class CiotDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    motorista_id: uuid.UUID
    codigo_ciot: str | None
    status: str
    protocolo_antt: str | None
    data_hora_registro: datetime | None

    @staticmethod
    def from_entity(entity: Ciot) -> "CiotDTO":
        return CiotDTO(
            id=entity.id, viagem_id=entity.viagem_id, motorista_id=entity.motorista_id,
            codigo_ciot=entity.codigo_ciot, status=entity.status.value, protocolo_antt=entity.protocolo_antt,
            data_hora_registro=entity.data_hora_registro,
        )
