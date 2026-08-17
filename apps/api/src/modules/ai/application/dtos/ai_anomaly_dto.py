from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.ai.domain.entities.ai_anomaly import AIAnomaly


@dataclass(frozen=True)
class AIAnomalyDTO:
    id: uuid.UUID
    inference_id: uuid.UUID
    source_reading_type: str
    source_reading_id: uuid.UUID
    confidence_level: Decimal
    status: str

    @staticmethod
    def from_entity(anomaly: AIAnomaly) -> "AIAnomalyDTO":
        return AIAnomalyDTO(
            id=anomaly.id, inference_id=anomaly.inferencia_ia_id,
            source_reading_type=anomaly.leitura_origem_tipo, source_reading_id=anomaly.leitura_origem_id,
            confidence_level=anomaly.nivel_confianca, status=anomaly.status.value,
        )
