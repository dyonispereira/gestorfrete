from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.identity_access.application.dtos.permission_dto import PermissionDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListPermissionsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    module: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class ListPermissionsResult:
    items: list[PermissionDTO]
    total: int


class ListPermissionsHandler(QueryHandler[ListPermissionsQuery, ListPermissionsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListPermissionsQuery) -> ListPermissionsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyPermissionRepository(session)
            permissions, total = await repo.list_page(
                page=query.page, limit=query.limit, module=query.module, search=query.search
            )
        return ListPermissionsResult(items=[PermissionDTO.from_entity(p) for p in permissions], total=total)


@dataclass(frozen=True)
class GetPermissionQuery(Query):
    actor: AuthenticatedActor
    permission_id: uuid.UUID


class GetPermissionHandler(QueryHandler[GetPermissionQuery, PermissionDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetPermissionQuery) -> PermissionDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyPermissionRepository(session)
            permission = await repo.get_by_id(query.permission_id)
        if permission is None:
            raise NotFoundError("IDENTITY_PERMISSION_NOT_FOUND", "Permissão não encontrada.")
        return PermissionDTO.from_entity(permission)
