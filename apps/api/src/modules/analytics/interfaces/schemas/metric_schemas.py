from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.analytics.application.dtos.metric_dto import MetricDTO


class CreateMetricRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    formula: str
    temporal_granularity: str
    dimensional_granularity: str
    unit: str
    data_sources: dict[str, Any] | None = None
    calculation_periodicity: str


class UpdateMetricRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    formula: str | None = None
    unit: str | None = None
    data_sources: dict[str, Any] | None = None
    calculation_periodicity: str | None = None
    status: str | None = None


class MetricResponse(BaseModel):
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
    def from_dto(dto: MetricDTO) -> "MetricResponse":
        return MetricResponse(
            id=dto.id, name=dto.name, formula=dto.formula, version=dto.version,
            temporal_granularity=dto.temporal_granularity, dimensional_granularity=dto.dimensional_granularity,
            unit=dto.unit, data_sources=dto.data_sources, calculation_periodicity=dto.calculation_periodicity,
            status=dto.status,
        )
