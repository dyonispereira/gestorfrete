from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.documents.domain.entities.mdfe_status_history_entry import MdfeStatusHistoryEntry


class MdfeStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: MdfeStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def count_for_mdfe(self, mdfe_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def list_page(
        self, mdfe_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[MdfeStatusHistoryEntry]: ...
