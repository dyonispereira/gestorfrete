from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.ai.domain.entities.ai_feedback import AIFeedback


@dataclass(frozen=True)
class AIFeedbackDTO:
    id: uuid.UUID
    output_type: str
    output_id: uuid.UUID
    user_id: uuid.UUID
    result: str
    justification: str | None
    actual_result: str | None
    created_at: datetime

    @staticmethod
    def from_entity(feedback: AIFeedback) -> "AIFeedbackDTO":
        return AIFeedbackDTO(
            id=feedback.id, output_type=feedback.saida_ia_tipo.value, output_id=feedback.saida_ia_id,
            user_id=feedback.usuario_id, result=feedback.resultado.value,
            justification=feedback.justificativa, actual_result=feedback.resultado_real,
            created_at=feedback.criado_em,
        )
