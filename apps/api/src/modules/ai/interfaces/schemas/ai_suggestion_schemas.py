from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.ai.application.dtos.ai_suggestion_dto import AISuggestionDTO


class RejectSuggestionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str | None = None


class AISuggestionResponse(BaseModel):
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
    def from_dto(dto: AISuggestionDTO) -> "AISuggestionResponse":
        return AISuggestionResponse(
            id=dto.id, inference_id=dto.inference_id, category=dto.category,
            target_entity_type=dto.target_entity_type, target_entity_id=dto.target_entity_id,
            recommendation=dto.recommendation, justification=dto.justification,
            confidence_level=dto.confidence_level, status=dto.status,
            decision_user_id=dto.decision_user_id, decided_at=dto.decided_at,
        )
