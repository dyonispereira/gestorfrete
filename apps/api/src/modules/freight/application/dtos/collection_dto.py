from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.freight.domain.entities.collection import Collection


@dataclass(frozen=True)
class CollectionDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    data_hora: datetime
    conferencia_ok: bool
    trip_status_operacional: str
    """D238-style — a Coleta é a transição `EM_DESLOCAMENTO → CARREGANDO` em si; o Frontend recebe
    o novo status junto da resposta, nunca precisa de um segundo GET para saber o resultado."""

    @staticmethod
    def from_entity(collection: Collection, *, trip_status_operacional: str) -> "CollectionDTO":
        return CollectionDTO(
            id=collection.id, viagem_id=collection.viagem_id, data_hora=collection.data_hora,
            conferencia_ok=collection.conferencia_ok, trip_status_operacional=trip_status_operacional,
        )
