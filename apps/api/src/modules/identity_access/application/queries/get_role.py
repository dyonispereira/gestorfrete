from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
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
class GetRoleQuery(Query):
    actor: AuthenticatedActor
    role_id: uuid.UUID


class GetRoleHandler(QueryHandler[GetRoleQuery, RoleDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetRoleQuery) -> RoleDTO:
        async with self._session_factory() as session:
            role_repo = SqlAlchemyRoleRepository(session)
            permission_repo = SqlAlchemyPermissionRepository(session)
            role = await role_repo.get_by_id(query.role_id)
            if role is None:
                raise NotFoundError("IDENTITY_ROLE_NOT_FOUND", "Papel não encontrado.")
            permissions = await permission_repo.get_by_ids(role.permission_ids)
        return RoleDTO.from_entity(role, [p.code for p in permissions])
