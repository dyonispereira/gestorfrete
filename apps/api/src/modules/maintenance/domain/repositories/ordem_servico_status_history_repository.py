from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry


class OrdemServicoStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: OrdemServicoStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def list_page(
        self, ordem_servico_id: uuid.UUID, *, after_data_hora: datetime | None, after_id: uuid.UUID | None,
        limit: int, status: str | None,
    ) -> list[OrdemServicoStatusHistoryEntry]: ...
