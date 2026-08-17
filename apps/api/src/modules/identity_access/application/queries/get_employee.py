from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.identity_access.application.dtos.employee_dto import EmployeeDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_employee_repository import (
    SqlAlchemyEmployeeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetEmployeeQuery(Query):
    actor: AuthenticatedActor
    employee_id: uuid.UUID


class GetEmployeeHandler(QueryHandler[GetEmployeeQuery, EmployeeDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetEmployeeQuery) -> EmployeeDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyEmployeeRepository(session)
            employee = await repo.get_by_id(query.employee_id)
        if employee is None:
            raise NotFoundError("IDENTITY_EMPLOYEE_NOT_FOUND", "Funcionário não encontrado.")
        return EmployeeDTO.from_entity(employee)
