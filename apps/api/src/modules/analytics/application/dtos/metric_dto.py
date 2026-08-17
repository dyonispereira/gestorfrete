from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from modules.analytics.domain.entities.metric import Metric


@dataclass(frozen=True)
class MetricDTO:
    id: uuid.UUID
    name: str
    formula: str
    version: int
    temporal_granularity: str
    dimensional_granularity: str
    unit: str
    data_sources: dict[str, Any]
    calculation_periodicity: str
    status: str

    @staticmethod
    def from_entity(metric: Metric) -> "MetricDTO":
        return MetricDTO(
            id=metric.id, name=metric.nome, formula=metric.formula, version=metric.versao,
            temporal_granularity=metric.granularidade_temporal.value,
            dimensional_granularity=metric.granularidade_dimensional.value, unit=metric.unidade,
            data_sources=metric.origem_dados, calculation_periodicity=metric.periodicidade_calculo.value,
            status=metric.status.value,
        )
