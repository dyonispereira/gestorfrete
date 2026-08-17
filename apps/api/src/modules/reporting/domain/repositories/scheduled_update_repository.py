from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.reporting.domain.entities.scheduled_update import ScheduledUpdate


class ScheduledUpdateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ScheduledUpdate | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, metric_id: uuid.UUID | None, cube_id: uuid.UUID | None, mode: str | None,
        status: str | None,
    ) -> tuple[list[ScheduledUpdate], int]: ...

    @abstractmethod
    async def add(self, scheduled_update: ScheduledUpdate) -> None: ...
