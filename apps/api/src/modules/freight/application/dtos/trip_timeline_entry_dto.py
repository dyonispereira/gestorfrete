from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TripTimelineEntryDTO:
    occurred_at: datetime
    source: str
    summary: str
    reference_id: uuid.UUID
