from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.freight.domain.entities.trip_allocation import TripAllocation


@dataclass(frozen=True)
class TripAllocationDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    motorista_id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    implemento_id: uuid.UUID | None
    status: str
    motivo_troca: str | None
    criado_em: datetime

    @staticmethod
    def from_entity(allocation: TripAllocation) -> "TripAllocationDTO":
        return TripAllocationDTO(
            id=allocation.id,
            viagem_id=allocation.viagem_id,
            motorista_id=allocation.motorista_id,
            veiculo_tracionador_id=allocation.veiculo_tracionador_id,
            implemento_id=allocation.implemento_id,
            status=allocation.status.value,
            motivo_troca=allocation.motivo_troca,
            criado_em=allocation.criado_em,
        )
