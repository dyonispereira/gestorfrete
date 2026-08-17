from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.integration.application.dtos.job_execution_dto import JobExecutionDTO


class TriggerJobRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_type: str
    parameters: dict[str, Any] | None = None


class JobExecutionResponse(BaseModel):
    id: uuid.UUID
    job_type: str
    started_at: datetime
    finished_at: datetime | None
    result: str | None

    @staticmethod
    def from_dto(dto: JobExecutionDTO) -> "JobExecutionResponse":
        return JobExecutionResponse(
            id=dto.id, job_type=dto.job_type, started_at=dto.started_at, finished_at=dto.finished_at,
            result=dto.result,
        )
