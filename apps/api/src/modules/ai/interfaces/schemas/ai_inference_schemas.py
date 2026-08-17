from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from modules.ai.application.dtos.ai_inference_dto import AIInferenceDTO


class AIInferenceResponse(BaseModel):
    """D172 — auditável. `cost` só é preenchido com `ai.inference.view_cost` (auditoria 7); sem a
    permissão, é sempre `None`, nunca omitido do schema."""

    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    confidence_level: Decimal | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    cost: Decimal | None
    attempt_number: int
    origin: str
    status: str

    @staticmethod
    def from_dto(dto: AIInferenceDTO) -> "AIInferenceResponse":
        return AIInferenceResponse(
            id=dto.id, model_id=dto.model_id, model_version=dto.model_version, input=dto.input,
            output=dto.output, confidence_level=dto.confidence_level, started_at=dto.started_at,
            finished_at=dto.finished_at, duration_ms=dto.duration_ms, cost=dto.cost,
            attempt_number=dto.attempt_number, origin=dto.origin, status=dto.status,
        )
