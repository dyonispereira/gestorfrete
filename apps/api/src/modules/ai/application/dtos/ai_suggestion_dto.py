from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.ai.domain.entities.ai_suggestion import AISuggestion


@dataclass(frozen=True)
class AISuggestionDTO:
    id: uuid.UUID
    inference_id: uuid.UUID
    category: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    recommendation: str
    justification: str
    confidence_level: Decimal
    status: str
    decision_user_id: uuid.UUID | None
    decided_at: datetime | None

    @staticmethod
    def from_entity(suggestion: AISuggestion) -> "AISuggestionDTO":
        return AISuggestionDTO(
            id=suggestion.id, inference_id=suggestion.inferencia_ia_id, category=suggestion.categoria,
            target_entity_type=suggestion.entidade_alvo_tipo, target_entity_id=suggestion.entidade_alvo_id,
            recommendation=suggestion.recomendacao, justification=suggestion.justificativa,
            confidence_level=suggestion.nivel_confianca, status=suggestion.status.value,
            decision_user_id=suggestion.usuario_decisao_id, decided_at=suggestion.data_hora_decisao,
        )
