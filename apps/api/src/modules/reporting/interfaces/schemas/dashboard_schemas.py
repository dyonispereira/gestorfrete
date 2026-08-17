from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.reporting.application.dtos.dashboard_dto import DashboardDTO


class CreateDashboardRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    layout: dict[str, Any]
    widgets: list[dict[str, Any]]
    filters: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None


class UpdateDashboardRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    layout: dict[str, Any] | None = None
    widgets: list[dict[str, Any]] | None = None
    filters: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None
    status: str | None = None


class ShareDashboardRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sharing: str


class DashboardResponse(BaseModel):
    """Sem `audit` — `dashboards_personalizados` não tem nenhuma coluna de auditoria na DDL
    congelada (D422)."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    layout: dict[str, Any]
    widgets: list[dict[str, Any]]
    filters: dict[str, Any] | None
    sharing: str
    preferences: dict[str, Any] | None
    status: str

    @staticmethod
    def from_dto(dto: DashboardDTO) -> "DashboardResponse":
        return DashboardResponse(
            id=dto.id, user_id=dto.user_id, name=dto.name, layout=dto.layout, widgets=dto.widgets,
            filters=dto.filters, sharing=dto.sharing, preferences=dto.preferences, status=dto.status,
        )
