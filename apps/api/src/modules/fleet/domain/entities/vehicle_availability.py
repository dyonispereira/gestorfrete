from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.value_objects.availability_status import AvailabilityStatus


@dataclass(frozen=True)
class VehicleAvailability:
    """Read Model puro (D081) — não é `BaseEntity`/`BaseAggregateRoot` (não pertence a nenhum
    agregado transacional, nunca grava Domain Event). `veiculo_tracionador_id` é a própria PK
    física (`AVAILABILITY_IMPLEMENTATION.md`)."""

    veiculo_tracionador_id: uuid.UUID
    status: AvailabilityStatus
    motorista_atual_id: uuid.UUID | None
    implemento_atual_id: uuid.UUID | None
    atualizado_em: datetime
