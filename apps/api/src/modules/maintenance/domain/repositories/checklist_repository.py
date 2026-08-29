from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.maintenance.domain.entities.checklist import Checklist
from shared_kernel.domain.repository import Repository


class ChecklistRepository(Repository[Checklist, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, referencia_tipo: str | None, referencia_id: uuid.UUID | None,
        tipo: str | None, status: str | None,
    ) -> tuple[list[Checklist], int]: ...
