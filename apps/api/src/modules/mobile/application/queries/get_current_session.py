from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.mobile.application.dtos.mobile_session_dto import MobileSessionDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_session_repository import (
    SqlAlchemyMobileSessionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetCurrentSessionQuery(Query):
    actor: AuthenticatedActor


@dataclass(frozen=True)
class GetCurrentSessionResult:
    session: MobileSessionDTO
    driver: DriverDTO


class GetCurrentSessionHandler(QueryHandler[GetCurrentSessionQuery, GetCurrentSessionResult]):
    """`GET /mobile/auth/me` — nenhuma permissão além de autenticado."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetCurrentSessionQuery) -> GetCurrentSessionResult:
        async with self._session_factory() as session:
            session_repo = SqlAlchemyMobileSessionRepository(session)
            mobile_session = await session_repo.get_by_id(query.actor.session_id)
            if mobile_session is None:
                raise NotFoundError("MOBILE_SESSION_NOT_FOUND", "Sessão Mobile não encontrada.")

            driver_repo = SqlAlchemyDriverRepository(session)
            driver = await driver_repo.get_by_id(mobile_session.motorista_id)
            if driver is None:
                raise NotFoundError("MOBILE_SESSION_NOT_FOUND", "Motorista da sessão não encontrado.")

        return GetCurrentSessionResult(
            session=MobileSessionDTO.from_entity(mobile_session), driver=DriverDTO.from_entity(driver)
        )
