from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.integration.domain.entities.job_execution import JobExecution


class JobExecutionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> JobExecution | None: ...

    @abstractmethod
    async def list_cursor(
        self, *, limit: int, job_type: str | None, result: str | None, started_from: datetime | None,
        started_to: datetime | None, after_data_hora_inicio: datetime | None, after_id: uuid.UUID | None,
    ) -> list[JobExecution]: ...

    @abstractmethod
    async def add(self, execution: JobExecution) -> None: ...
