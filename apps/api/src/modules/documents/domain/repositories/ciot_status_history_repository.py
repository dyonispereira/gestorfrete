from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.documents.domain.entities.ciot_status_history_entry import CiotStatusHistoryEntry


class CiotStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: CiotStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def count_for_ciot(self, ciot_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def list_page(
        self, ciot_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[CiotStatusHistoryEntry]: ...
