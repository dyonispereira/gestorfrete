from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.ai.domain.entities.ai_prediction import AIPrediction


@dataclass(frozen=True)
class AIPredictionDTO:
    id: uuid.UUID
    inference_id: uuid.UUID
    category: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    predicted_value: Decimal
    confidence_level: Decimal
    valid_until: datetime
    status: str

    @staticmethod
    def from_entity(prediction: AIPrediction, *, now: datetime) -> "AIPredictionDTO":
        """D312/D425 — `status` é sempre o EFETIVO (recalculado contra `now`), nunca o valor físico
        gravado cegamente."""

        return AIPredictionDTO(
            id=prediction.id, inference_id=prediction.inferencia_ia_id, category=prediction.categoria,
            target_entity_type=prediction.entidade_alvo_tipo, target_entity_id=prediction.entidade_alvo_id,
            predicted_value=prediction.valor_previsto, confidence_level=prediction.nivel_confianca,
            valid_until=prediction.data_hora_validade_fim,
            status=prediction.effective_status(now=now).value,
        )
