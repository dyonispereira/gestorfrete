from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.integration_config_dto import IntegrationConfigDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_integration_config_repository import (
    SqlAlchemyIntegrationConfigRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetIntegrationConfigQuery(Query):
    actor: AuthenticatedActor
    config_id: uuid.UUID


class GetIntegrationConfigHandler(QueryHandler[GetIntegrationConfigQuery, IntegrationConfigDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetIntegrationConfigQuery) -> IntegrationConfigDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyIntegrationConfigRepository(session)
            config = await repo.get_by_id(query.config_id)
        if config is None:
            raise NotFoundError("INTEGRATION_CONFIG_NOT_FOUND", "Configuração de Integração não encontrada.")
        return IntegrationConfigDTO.from_entity(config)
