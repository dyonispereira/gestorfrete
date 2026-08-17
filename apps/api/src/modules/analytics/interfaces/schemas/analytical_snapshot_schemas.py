from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.analytics.application.dtos.analytical_snapshot_dto import AnalyticalSnapshotDTO


class CreateSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reference_period: str


class ParticipatingMetricResponse(BaseModel):
    metric_id: uuid.UUID
    metric_version: int


class AnalyticalSnapshotResponse(BaseModel):
    id: uuid.UUID
    reference_period: str
    consolidated_at: datetime | None
    processing_origin: str
    user_id: uuid.UUID | None
    participating_metrics: list[ParticipatingMetricResponse]
    indicator_ids: list[uuid.UUID]
    status: str

    @staticmethod
    def from_dto(dto: AnalyticalSnapshotDTO) -> "AnalyticalSnapshotResponse":
        return AnalyticalSnapshotResponse(
            id=dto.id, reference_period=dto.reference_period, consolidated_at=dto.consolidated_at,
            processing_origin=dto.processing_origin, user_id=dto.user_id,
            participating_metrics=[
                ParticipatingMetricResponse(metric_id=p.metric_id, metric_version=p.metric_version)
                for p in dto.participating_metrics
            ],
            indicator_ids=dto.indicator_ids, status=dto.status,
        )
