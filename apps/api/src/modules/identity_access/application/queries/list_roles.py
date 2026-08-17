from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.identity_access.application.dtos.role_dto import RoleDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListRolesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None


@dataclass(frozen=True)
class ListRolesResult:
    items: list[RoleDTO]
    total: int


class ListRolesHandler(QueryHandler[ListRolesQuery, ListRolesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListRolesQuery) -> ListRolesResult:
        async with self._session_factory() as session:
            role_repo = SqlAlchemyRoleRepository(session)
            permission_repo = SqlAlchemyPermissionRepository(session)
            roles, total = await role_repo.list_page(page=query.page, limit=query.limit, search=query.search)
            items = []
            for role in roles:
                permissions = await permission_repo.get_by_ids(role.permission_ids)
                items.append(RoleDTO.from_entity(role, [p.code for p in permissions]))
        return ListRolesResult(items=items, total=total)
