from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.analytics.domain.entities.analytics_cube import AnalyticsCube


class AnalyticsCubeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AnalyticsCube | None: ...

    @abstractmethod
    async def exists_with_name(self, tenant_id: uuid.UUID, nome: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, status: str | None
    ) -> tuple[list[AnalyticsCube], int]: ...

    @abstractmethod
    async def add(self, cube: AnalyticsCube) -> None: ...
