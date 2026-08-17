from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.reporting.domain.entities.export import Export


class ExportRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Export | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None, saved_report_id: uuid.UUID | None, usuario_id: uuid.UUID
    ) -> tuple[list[Export], int]: ...

    @abstractmethod
    async def add(self, export: Export) -> None: ...
