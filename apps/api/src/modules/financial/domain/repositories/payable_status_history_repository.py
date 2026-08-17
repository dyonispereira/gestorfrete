from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry


class PayableStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: PayableStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[PayableStatusHistoryEntry]: ...
