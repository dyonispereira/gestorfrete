from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.identity_access.application.dtos.employee_dto import EmployeeDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_employee_repository import (
    SqlAlchemyEmployeeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListEmployeesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


@dataclass(frozen=True)
class ListEmployeesResult:
    items: list[EmployeeDTO]
    total: int


class ListEmployeesHandler(QueryHandler[ListEmployeesQuery, ListEmployeesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListEmployeesQuery) -> ListEmployeesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyEmployeeRepository(session)
            employees, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                status=query.status,
                search=query.search,
                created_from=query.created_from,
                created_to=query.created_to,
            )
        return ListEmployeesResult(items=[EmployeeDTO.from_entity(e) for e in employees], total=total)
