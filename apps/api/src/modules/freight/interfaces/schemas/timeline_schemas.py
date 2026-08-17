from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.freight.application.dtos.trip_timeline_entry_dto import TripTimelineEntryDTO


class TripTimelineEntryResponse(BaseModel):
    occurred_at: datetime
    source: str
    summary: str
    reference_id: uuid.UUID

    @staticmethod
    def from_dto(dto: TripTimelineEntryDTO) -> "TripTimelineEntryResponse":
        return TripTimelineEntryResponse(
            occurred_at=dto.occurred_at, source=dto.source, summary=dto.summary, reference_id=dto.reference_id
        )
