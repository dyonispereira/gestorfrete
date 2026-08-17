from __future__ import annotations

import uuid
from datetime import datetime

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.domain.value_objects.job_result import JobResult
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_job_execution_repository import (
    SqlAlchemyJobExecutionRepository,
)


class JobInternalTransitions:
    """D322/D413 — a execução real de um Job fica em processo de background fora deste contrato
    (`089-jobs.md`: "este endpoint só cria o registro e enfileira o disparo"). Mesmo espírito de
    `TripInternalTransitions` — nunca alcançável por HTTP, só chamado diretamente por teste,
    simulando o worker que este lote não constrói."""

    async def complete_job(self, *, job_id: uuid.UUID, result: JobResult, now: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyJobExecutionRepository(uow.session)
            execution = await repo.get_by_id(job_id)
            if execution is None:
                raise NotFoundError("INTEGRATION_JOB_NOT_FOUND", "Execução de Job não encontrada.")
            execution.complete(resultado=result, now=now)
            await repo.add(execution)
            await uow.commit()
