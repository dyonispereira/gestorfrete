from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.documents.application.dtos.status_history_entry_dto import StatusHistoryEntryDTO


class StatusHistoryEntryResponse(BaseModel):
    """Compartilhado por CT-e/MDF-e/CIOT status-history (D284 — mesmos campos padrão nos três)."""

    id: uuid.UUID
    status: str
    user_id: uuid.UUID | None
    origin: str
    notes: str | None
    occurred_at: datetime

    @staticmethod
    def from_dto(dto: StatusHistoryEntryDTO) -> "StatusHistoryEntryResponse":
        return StatusHistoryEntryResponse(
            id=dto.id, status=dto.status, user_id=dto.user_id, origin=dto.origin, notes=dto.notes,
            occurred_at=dto.occurred_at,
        )
