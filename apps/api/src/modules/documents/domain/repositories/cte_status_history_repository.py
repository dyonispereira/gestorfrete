from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.documents.domain.entities.cte_status_history_entry import CteStatusHistoryEntry


class CteStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: CteStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def count_for_cte(self, cte_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def list_page(
        self, cte_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[CteStatusHistoryEntry]: ...
