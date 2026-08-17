from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.analytics.domain.entities.analytical_snapshot import AnalyticalSnapshot


class AnalyticalSnapshotRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AnalyticalSnapshot | None: ...

    @abstractmethod
    async def get_consolidated_for_period(self, periodo_referencia: str) -> AnalyticalSnapshot | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, reference_period: str | None, processing_origin: str | None,
        status: str | None,
    ) -> tuple[list[AnalyticalSnapshot], int]: ...

    @abstractmethod
    async def list_indicator_ids(self, snapshot_id: uuid.UUID) -> list[uuid.UUID]: ...

    @abstractmethod
    async def get_participating_metrics(self, snapshot_id: uuid.UUID) -> list[tuple[uuid.UUID, int]]:
        """D160 — `{metric_id, metric_version}` distintos, derivados via junção com
        `indicadores_consolidados` (nunca uma coluna própria, ver `AnalyticalSnapshotModel`)."""
        ...

    @abstractmethod
    async def add(self, snapshot: AnalyticalSnapshot) -> None: ...

    @abstractmethod
    async def link_indicators(self, snapshot_id: uuid.UUID, indicator_ids: list[uuid.UUID]) -> None: ...
