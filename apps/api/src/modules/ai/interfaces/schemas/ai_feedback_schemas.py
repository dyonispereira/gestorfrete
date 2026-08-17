from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.ai.application.dtos.ai_feedback_dto import AIFeedbackDTO


class CreateAIFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    output_type: str
    output_id: uuid.UUID
    result: str
    justification: str | None = None
    actual_result: str | None = None


class UpdateAIFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    actual_result: str


class AIFeedbackResponse(BaseModel):
    id: uuid.UUID
    output_type: str
    output_id: uuid.UUID
    user_id: uuid.UUID
    result: str
    justification: str | None
    actual_result: str | None
    created_at: datetime

    @staticmethod
    def from_dto(dto: AIFeedbackDTO) -> "AIFeedbackResponse":
        return AIFeedbackResponse(
            id=dto.id, output_type=dto.output_type, output_id=dto.output_id, user_id=dto.user_id,
            result=dto.result, justification=dto.justification, actual_result=dto.actual_result,
            created_at=dto.created_at,
        )
