from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.reporting.domain.entities.saved_report import SavedReport


class SavedReportRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> SavedReport | None: ...

    @abstractmethod
    async def exists_with_name(self, usuario_id: uuid.UUID, nome: str) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, output_format: str | None, status: str | None,
        usuario_id: uuid.UUID,
    ) -> tuple[list[SavedReport], int]: ...

    @abstractmethod
    async def add(self, saved_report: SavedReport) -> None: ...
