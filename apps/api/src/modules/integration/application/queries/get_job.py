from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.job_execution_dto import JobExecutionDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_job_execution_repository import (
    SqlAlchemyJobExecutionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetJobQuery(Query):
    actor: AuthenticatedActor
    job_id: uuid.UUID


class GetJobHandler(QueryHandler[GetJobQuery, JobExecutionDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetJobQuery) -> JobExecutionDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyJobExecutionRepository(session)
            execution = await repo.get_by_id(query.job_id)
        if execution is None:
            raise NotFoundError("INTEGRATION_JOB_NOT_FOUND", "Execução de Job não encontrada.")
        return JobExecutionDTO.from_entity(execution)
