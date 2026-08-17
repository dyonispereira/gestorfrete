from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from modules.ai.application.dtos.ai_prediction_dto import AIPredictionDTO


class AIPredictionResponse(BaseModel):
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
    def from_dto(dto: AIPredictionDTO) -> "AIPredictionResponse":
        return AIPredictionResponse(
            id=dto.id, inference_id=dto.inference_id, category=dto.category,
            target_entity_type=dto.target_entity_type, target_entity_id=dto.target_entity_id,
            predicted_value=dto.predicted_value, confidence_level=dto.confidence_level,
            valid_until=dto.valid_until, status=dto.status,
        )
