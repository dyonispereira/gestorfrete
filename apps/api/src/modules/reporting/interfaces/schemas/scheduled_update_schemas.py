from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.reporting.application.dtos.scheduled_update_dto import ScheduledUpdateDTO
from modules.reporting.domain.value_objects.scheduled_update_mode import ScheduledUpdateMode


class CreateScheduledUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    metric_id: uuid.UUID | None = None
    cube_id: uuid.UUID | None = None
    mode: ScheduledUpdateMode


class UpdateScheduledUpdateRequest(BaseModel):
    """`metric_id`/`cube_id` (o alvo) não são editáveis após a criação — só `mode`/`status`."""

    model_config = ConfigDict(extra="ignore")

    mode: ScheduledUpdateMode | None = None
    status: str | None = None


class ScheduledUpdateResponse(BaseModel):
    id: uuid.UUID
    metric_id: uuid.UUID | None
    cube_id: uuid.UUID | None
    mode: str
    status: str

    @staticmethod
    def from_dto(dto: ScheduledUpdateDTO) -> "ScheduledUpdateResponse":
        return ScheduledUpdateResponse(
            id=dto.id, metric_id=dto.metric_id, cube_id=dto.cube_id, mode=dto.mode, status=dto.status,
        )
