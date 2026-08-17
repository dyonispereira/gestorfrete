from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.analytics.domain.entities.analytics_cube import AnalyticsCube


@dataclass(frozen=True)
class AnalyticsCubeDTO:
    id: uuid.UUID
    name: str
    dimensions: list[str]
    metric_ids: list[uuid.UUID]
    status: str

    @staticmethod
    def from_entity(cube: AnalyticsCube) -> "AnalyticsCubeDTO":
        return AnalyticsCubeDTO(
            id=cube.id, name=cube.nome, dimensions=cube.dimensoes, metric_ids=cube.metricas_ids,
            status=cube.status,
        )
