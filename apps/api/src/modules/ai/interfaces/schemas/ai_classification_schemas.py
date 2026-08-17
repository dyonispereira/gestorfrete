from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from modules.ai.application.dtos.ai_classification_dto import AIClassificationDTO


class AIClassificationResponse(BaseModel):
    id: uuid.UUID
    inference_id: uuid.UUID
    classification_type: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    label: str
    confidence_level: Decimal
    created_at: datetime

    @staticmethod
    def from_dto(dto: AIClassificationDTO) -> "AIClassificationResponse":
        return AIClassificationResponse(
            id=dto.id, inference_id=dto.inference_id, classification_type=dto.classification_type,
            target_entity_type=dto.target_entity_type, target_entity_id=dto.target_entity_id,
            label=dto.label, confidence_level=dto.confidence_level, created_at=dto.created_at,
        )
