from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.speed_limit_config_dto import SpeedLimitConfigDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_speed_limit_config_repository import (
    SqlAlchemySpeedLimitConfigRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSpeedLimitConfigQuery(Query):
    actor: AuthenticatedActor
    speed_limit_config_id: uuid.UUID


class GetSpeedLimitConfigHandler(QueryHandler[GetSpeedLimitConfigQuery, SpeedLimitConfigDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSpeedLimitConfigQuery) -> SpeedLimitConfigDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemySpeedLimitConfigRepository(session)
            config = await repo.get_by_id(query.speed_limit_config_id)
        if config is None:
            raise NotFoundError("TRACKING_SPEED_LIMIT_CONFIG_NOT_FOUND", "Configuração de Limite de Velocidade não encontrada.")
        return SpeedLimitConfigDTO.from_entity(config)
