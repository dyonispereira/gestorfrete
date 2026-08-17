from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.analytics.domain.entities.metric import Metric


class MetricRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Metric | None: ...

    @abstractmethod
    async def get_latest_by_name(self, nome: str, *, tenant_id: uuid.UUID | None) -> Metric | None:
        """D419 — `ORDER BY versao DESC LIMIT 1`; "a versão atual" da Métrica por nome."""
        ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, temporal_granularity: str | None,
        dimensional_granularity: str | None, status: str | None,
    ) -> tuple[list[Metric], int]: ...

    @abstractmethod
    async def add(self, metric: Metric) -> None: ...
