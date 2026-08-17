from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from modules.analytics.application.dtos.consolidated_indicator_dto import ConsolidatedIndicatorDTO


class ConsolidatedIndicatorResponse(BaseModel):
    """Todo campo `readOnly` — nunca aceita fórmula/valor digitado (D156). Nunca inclui `formula`."""

    id: uuid.UUID
    metric_id: uuid.UUID
    metric_version: int
    dimension_type: str
    dimension_id: uuid.UUID
    reference_period: str
    value: Decimal
    calculated_at: datetime
    status: str

    @staticmethod
    def from_dto(dto: ConsolidatedIndicatorDTO) -> "ConsolidatedIndicatorResponse":
        return ConsolidatedIndicatorResponse(
            id=dto.id, metric_id=dto.metric_id, metric_version=dto.metric_version,
            dimension_type=dto.dimension_type, dimension_id=dto.dimension_id,
            reference_period=dto.reference_period, value=dto.value, calculated_at=dto.calculated_at,
            status=dto.status,
        )
