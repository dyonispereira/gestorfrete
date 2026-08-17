from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from modules.reporting.domain.entities.dashboard import Dashboard


@dataclass(frozen=True)
class DashboardDTO:
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
    def from_entity(dashboard: Dashboard) -> "DashboardDTO":
        return DashboardDTO(
            id=dashboard.id, user_id=dashboard.usuario_id, name=dashboard.nome, layout=dashboard.layout,
            widgets=dashboard.widgets, filters=dashboard.filtros,
            sharing=dashboard.permissoes_compartilhamento.value, preferences=dashboard.preferencias,
            status=dashboard.status,
        )
