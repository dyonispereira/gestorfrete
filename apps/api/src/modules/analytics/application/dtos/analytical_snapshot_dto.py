from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.analytics.domain.entities.analytical_snapshot import AnalyticalSnapshot


@dataclass(frozen=True)
class ParticipatingMetricDTO:
    metric_id: uuid.UUID
    metric_version: int


@dataclass(frozen=True)
class AnalyticalSnapshotDTO:
    id: uuid.UUID
    reference_period: str
    consolidated_at: datetime | None
    processing_origin: str
    user_id: uuid.UUID | None
    participating_metrics: list[ParticipatingMetricDTO]
    indicator_ids: list[uuid.UUID]
    status: str

    @staticmethod
    def from_entity(
        snapshot: AnalyticalSnapshot, *, participating_metrics: list[ParticipatingMetricDTO],
        indicator_ids: list[uuid.UUID],
    ) -> "AnalyticalSnapshotDTO":
        return AnalyticalSnapshotDTO(
            id=snapshot.id, reference_period=snapshot.periodo_referencia,
            consolidated_at=snapshot.data_hora_consolidacao, processing_origin=snapshot.origem_processamento.value,
            user_id=snapshot.usuario_id, participating_metrics=participating_metrics, indicator_ids=indicator_ids,
            status=snapshot.status.value,
        )
