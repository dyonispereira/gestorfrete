from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.reporting.domain.entities.scheduled_update import ScheduledUpdate


@dataclass(frozen=True)
class ScheduledUpdateDTO:
    id: uuid.UUID
    metric_id: uuid.UUID | None
    cube_id: uuid.UUID | None
    mode: str
    status: str

    @staticmethod
    def from_entity(scheduled_update: ScheduledUpdate) -> "ScheduledUpdateDTO":
        return ScheduledUpdateDTO(
            id=scheduled_update.id, metric_id=scheduled_update.metrica_id,
            cube_id=scheduled_update.cubo_analitico_id, mode=scheduled_update.modo.value,
            status=scheduled_update.status,
        )
