from __future__ import annotations

import uuid
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
class GetDriverQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID


class GetDriverHandler(QueryHandler[GetDriverQuery, DriverDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetDriverQuery) -> DriverDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDriverRepository(session)
            driver = await repo.get_by_id(query.driver_id)
        if driver is None:
            raise NotFoundError("DRIVERS_DRIVER_NOT_FOUND", "Motorista não encontrado.")
        return DriverDTO.from_entity(driver)
