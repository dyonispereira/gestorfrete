from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetMyDriverQuery(Query):
    actor: AuthenticatedActor


class GetMyDriverHandler(QueryHandler[GetMyDriverQuery, DriverDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetMyDriverQuery) -> DriverDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDriverRepository(session)
            driver = await repo.get_by_user_id(query.actor.user_id)
        if driver is None:
            raise NotFoundError(
                "DRIVERS_NOT_A_DRIVER_ACCOUNT", "O usuário autenticado não tem um cadastro de Motorista vinculado."
            )
        return DriverDTO.from_entity(driver)
