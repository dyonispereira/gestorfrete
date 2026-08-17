from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.receivable_status_history_entry import ReceivableStatusHistoryEntry


class ReceivableStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: ReceivableStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def list_for_receivable(self, conta_receber_id: uuid.UUID) -> list[ReceivableStatusHistoryEntry]: ...
