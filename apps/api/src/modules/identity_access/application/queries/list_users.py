from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListUsersQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    role_id: uuid.UUID | None = None
    search: str | None = None


@dataclass(frozen=True)
class ListUsersResult:
    items: list[UserDTO]
    total: int


class ListUsersHandler(QueryHandler[ListUsersQuery, ListUsersResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListUsersQuery) -> ListUsersResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyUserRepository(session)
            users, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, role_id=query.role_id, search=query.search
            )
        return ListUsersResult(items=[UserDTO.from_entity(u) for u in users], total=total)
