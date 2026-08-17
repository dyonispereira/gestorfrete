from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.ai.application.dtos.ai_anomaly_dto import AIAnomalyDTO


class ReviewAnomalyRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resolution: str
    notes: str | None = None


class AIAnomalyResponse(BaseModel):
    id: uuid.UUID
    inference_id: uuid.UUID
    source_reading_type: str
    source_reading_id: uuid.UUID
    confidence_level: Decimal
    status: str

    @staticmethod
    def from_dto(dto: AIAnomalyDTO) -> "AIAnomalyResponse":
        return AIAnomalyResponse(
            id=dto.id, inference_id=dto.inference_id, source_reading_type=dto.source_reading_type,
            source_reading_id=dto.source_reading_id, confidence_level=dto.confidence_level, status=dto.status,
        )
