from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from modules.reporting.domain.entities.saved_report import SavedReport


@dataclass(frozen=True)
class SavedReportDTO:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    metric_ids: list[uuid.UUID]
    filters: dict[str, Any] | None
    output_format: str
    status: str

    @staticmethod
    def from_entity(saved_report: SavedReport) -> "SavedReportDTO":
        return SavedReportDTO(
            id=saved_report.id, user_id=saved_report.usuario_id, name=saved_report.nome,
            metric_ids=saved_report.metricas_ids, filters=saved_report.filtros,
            output_format=saved_report.formato_saida.value, status=saved_report.status,
        )
