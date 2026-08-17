from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.ai.application.dtos.computer_vision_reading_dto import ComputerVisionReadingDTO


class RejectComputerVisionReadingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reason: str


class ComputerVisionReadingResponse(BaseModel):
    id: uuid.UUID
    inference_id: uuid.UUID
    source_file_id: uuid.UUID
    reading_type: str
    analyzed_region: dict[str, Any] | None
    extracted_result: dict[str, Any]
    confidence_level: Decimal
    human_review_required: bool
    status: str
    confirmation_user_id: uuid.UUID | None

    @staticmethod
    def from_dto(dto: ComputerVisionReadingDTO) -> "ComputerVisionReadingResponse":
        return ComputerVisionReadingResponse(
            id=dto.id, inference_id=dto.inference_id, source_file_id=dto.source_file_id,
            reading_type=dto.reading_type, analyzed_region=dto.analyzed_region,
            extracted_result=dto.extracted_result, confidence_level=dto.confidence_level,
            human_review_required=dto.human_review_required, status=dto.status,
            confirmation_user_id=dto.confirmation_user_id,
        )
