from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.reporting.application.dtos.saved_report_dto import SavedReportDTO


class CreateSavedReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    metric_ids: list[uuid.UUID]
    filters: dict[str, Any] | None = None
    output_format: str


class UpdateSavedReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    metric_ids: list[uuid.UUID] | None = None
    filters: dict[str, Any] | None = None
    output_format: str | None = None
    status: str | None = None


class SavedReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    metric_ids: list[uuid.UUID]
    filters: dict[str, Any] | None
    output_format: str
    status: str

    @staticmethod
    def from_dto(dto: SavedReportDTO) -> "SavedReportResponse":
        return SavedReportResponse(
            id=dto.id, user_id=dto.user_id, name=dto.name, metric_ids=dto.metric_ids, filters=dto.filters,
            output_format=dto.output_format, status=dto.status,
        )
