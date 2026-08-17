from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import ValidationError
from modules.integration.application.dtos.job_execution_dto import JobExecutionDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_job_execution_repository import (
    SqlAlchemyJobExecutionRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListJobsQuery(Query):
    actor: AuthenticatedActor
    cursor: str | None
    limit: int
    job_type: str | None
    result: str | None
    started_at_gte: datetime | None
    started_at_lte: datetime | None


@dataclass(frozen=True)
class ListJobsResult:
    items: list[JobExecutionDTO]
    next_cursor: str | None
    has_more: bool


class ListJobsHandler(QueryHandler[ListJobsQuery, ListJobsResult]):
    """D191/D287 — Time Series, cursor sempre, nunca offset."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListJobsQuery) -> ListJobsResult:
        after_started_at, after_id = None, None
        if query.cursor is not None:
            try:
                after_started_at, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("INTEGRATION_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            repo = SqlAlchemyJobExecutionRepository(session)
            executions = await repo.list_cursor(
                limit=query.limit + 1, job_type=query.job_type, result=query.result,
                started_from=query.started_at_gte, started_to=query.started_at_lte,
                after_data_hora_inicio=after_started_at, after_id=after_id,
            )

        has_more = len(executions) > query.limit
        page = executions[: query.limit]
        next_cursor = (
            encode_cursor(data_hora=page[-1].data_hora_inicio, id=page[-1].id) if has_more and page else None
        )
        return ListJobsResult(items=[JobExecutionDTO.from_entity(e) for e in page], next_cursor=next_cursor, has_more=has_more)
