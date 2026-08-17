from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.tracking.application.dtos.tracking_history_entry_dto import TrackingHistoryEntryDTO


class TrackingHistoryEntryResponse(BaseModel):
    occurred_at: datetime
    source: str
    summary: str
    reference_id: uuid.UUID

    @staticmethod
    def from_dto(dto: TrackingHistoryEntryDTO) -> "TrackingHistoryEntryResponse":
        return TrackingHistoryEntryResponse(
            occurred_at=dto.occurred_at, source=dto.source, summary=dto.summary, reference_id=dto.reference_id
        )
