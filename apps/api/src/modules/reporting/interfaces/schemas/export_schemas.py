from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.reporting.application.dtos.export_dto import ExportDTO


class CreateExportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    saved_report_id: uuid.UUID | None = None
    filters: dict[str, Any] | None = None
    period: str | None = None


class ExportResponse(BaseModel):
    """Filtros/período/versões de métrica são sempre resolvidos pela aplicação no momento da
    solicitação (D157) — nunca uma cópia do que o cliente enviou."""

    id: uuid.UUID
    saved_report_id: uuid.UUID | None
    user_id: uuid.UUID
    filters_used: dict[str, Any]
    period: str
    metric_versions: list[dict[str, Any]]
    file_id: uuid.UUID | None
    error_message: str | None
    requested_at: datetime
    status: str

    @staticmethod
    def from_dto(dto: ExportDTO) -> "ExportResponse":
        return ExportResponse(
            id=dto.id, saved_report_id=dto.saved_report_id, user_id=dto.user_id,
            filters_used=dto.filters_used, period=dto.period, metric_versions=dto.metric_versions,
            file_id=dto.file_id, error_message=dto.error_message, requested_at=dto.requested_at,
            status=dto.status,
        )
