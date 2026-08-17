from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from modules.reporting.domain.entities.export import Export


@dataclass(frozen=True)
class ExportDTO:
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
    def from_entity(export: Export) -> "ExportDTO":
        return ExportDTO(
            id=export.id, saved_report_id=export.relatorio_salvo_id, user_id=export.usuario_id,
            filters_used=export.filtros_utilizados, period=export.periodo,
            metric_versions=export.metricas_versoes, file_id=export.arquivo_id,
            error_message=export.mensagem_erro, requested_at=export.data_hora_solicitacao,
            status=export.status.value,
        )
