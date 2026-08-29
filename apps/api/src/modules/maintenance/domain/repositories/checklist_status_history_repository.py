from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry


class ChecklistStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: ChecklistStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def list_page(
        self, checklist_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[ChecklistStatusHistoryEntry]: ...
