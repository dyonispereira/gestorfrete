from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.integration.domain.entities.job_execution import JobExecution


@dataclass(frozen=True)
class JobExecutionDTO:
    id: uuid.UUID
    job_type: str
    started_at: datetime
    finished_at: datetime | None
    result: str | None

    @staticmethod
    def from_entity(execution: JobExecution) -> "JobExecutionDTO":
        return JobExecutionDTO(
            id=execution.id, job_type=execution.tipo_job, started_at=execution.data_hora_inicio,
            finished_at=execution.data_hora_fim, result=execution.resultado.value if execution.resultado else None,
        )
