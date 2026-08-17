from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.reporting.domain.entities.dashboard import Dashboard


class DashboardRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Dashboard | None: ...

    @abstractmethod
    async def exists_with_name(self, usuario_id: uuid.UUID, nome: str) -> bool: ...

    @abstractmethod
    async def list_own_and_shared(
        self, *, page: int, limit: int, search: str | None, status: str | None, usuario_id: uuid.UUID,
        include_shared: bool,
    ) -> tuple[list[Dashboard], int]: ...

    @abstractmethod
    async def add(self, dashboard: Dashboard) -> None: ...
