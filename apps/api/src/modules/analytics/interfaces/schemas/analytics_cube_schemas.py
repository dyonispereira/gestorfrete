from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.analytics.application.dtos.analytics_cube_dto import AnalyticsCubeDTO


class CreateAnalyticsCubeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    dimensions: list[str]
    metric_ids: list[uuid.UUID]


class UpdateAnalyticsCubeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dimensions: list[str] | None = None
    metric_ids: list[uuid.UUID] | None = None
    status: str | None = None


class AnalyticsCubeResponse(BaseModel):
    id: uuid.UUID
    name: str
    dimensions: list[str]
    metric_ids: list[uuid.UUID]
    status: str

    @staticmethod
    def from_dto(dto: AnalyticsCubeDTO) -> "AnalyticsCubeResponse":
        return AnalyticsCubeResponse(
            id=dto.id, name=dto.name, dimensions=dto.dimensions, metric_ids=dto.metric_ids, status=dto.status
        )
