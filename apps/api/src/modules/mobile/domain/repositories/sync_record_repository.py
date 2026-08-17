from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.mobile.domain.entities.sync_record import SyncRecord


class SyncRecordRepository(ABC):
    @abstractmethod
    async def add(self, record: SyncRecord) -> None: ...

    @abstractmethod
    async def list_page(
        self, *, sessao_mobile_id: uuid.UUID | None, page: int, limit: int
    ) -> tuple[list[SyncRecord], int]: ...
