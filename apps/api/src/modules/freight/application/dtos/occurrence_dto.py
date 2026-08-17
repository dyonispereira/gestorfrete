from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.freight.domain.entities.occurrence import Occurrence


@dataclass(frozen=True)
class OccurrenceDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    tipo: str
    descricao: str
    gravidade: str | None
    status: str
    data_hora: datetime

    @staticmethod
    def from_entity(occurrence: Occurrence) -> "OccurrenceDTO":
        return OccurrenceDTO(
            id=occurrence.id,
            viagem_id=occurrence.viagem_id,
            tipo=occurrence.tipo.value,
            descricao=occurrence.descricao,
            gravidade=occurrence.gravidade.value if occurrence.gravidade else None,
            status=occurrence.status.value,
            data_hora=occurrence.data_hora,
        )
