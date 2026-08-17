from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.ai.domain.entities.ai_classification import AIClassification


@dataclass(frozen=True)
class AIClassificationDTO:
    id: uuid.UUID
    inference_id: uuid.UUID
    classification_type: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    label: str
    confidence_level: Decimal
    created_at: datetime

    @staticmethod
    def from_entity(classification: AIClassification) -> "AIClassificationDTO":
        return AIClassificationDTO(
            id=classification.id, inference_id=classification.inferencia_ia_id,
            classification_type=classification.tipo_classificacao.value,
            target_entity_type=classification.entidade_alvo_tipo,
            target_entity_id=classification.entidade_alvo_id, label=classification.rotulo,
            confidence_level=classification.nivel_confianca, created_at=classification.criado_em,
        )
