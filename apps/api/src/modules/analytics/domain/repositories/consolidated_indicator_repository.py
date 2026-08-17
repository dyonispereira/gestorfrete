from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.analytics.domain.entities.consolidated_indicator import ConsolidatedIndicator


class ConsolidatedIndicatorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ConsolidatedIndicator | None: ...

    @abstractmethod
    async def get_latest(
        self, *, metrica_id: uuid.UUID, dimensao_tipo: str, dimensao_id: uuid.UUID, periodo_referencia: str
    ) -> ConsolidatedIndicator | None:
        """O indicador mais recente (qualquer status) para a tripla Métrica/dimensão/período —
        usado por `AnalyticsCalculationEngine` para decidir se um recálculo é permitido (D151: nunca
        se o mais recente já está `SNAPSHOTADO`)."""
        ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, metric_id: uuid.UUID | None, dimension_type: str | None,
        dimension_id: uuid.UUID | None, reference_period: str | None, status: str | None,
    ) -> tuple[list[ConsolidatedIndicator], int]: ...

    @abstractmethod
    async def add(self, indicator: ConsolidatedIndicator) -> None: ...
