from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.tracking.domain.entities.speed_limit_config import SpeedLimitConfig


@dataclass(frozen=True)
class SpeedLimitConfigDTO:
    id: uuid.UUID
    categoria_veiculo_id: uuid.UUID | None
    limite_kmh: float
    status: str

    @staticmethod
    def from_entity(entity: SpeedLimitConfig) -> "SpeedLimitConfigDTO":
        return SpeedLimitConfigDTO(
            id=entity.id, categoria_veiculo_id=entity.categoria_veiculo_id, limite_kmh=entity.limite_kmh,
            status=entity.status.value,
        )
