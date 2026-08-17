from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetUserQuery(Query):
    actor: AuthenticatedActor
    user_id: uuid.UUID


class GetUserHandler(QueryHandler[GetUserQuery, UserDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetUserQuery) -> UserDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyUserRepository(session)
            user = await repo.get_by_id(query.user_id)
        if user is None:
            raise NotFoundError("IDENTITY_USER_NOT_FOUND", "Usuário não encontrado.")
        return UserDTO.from_entity(user)
