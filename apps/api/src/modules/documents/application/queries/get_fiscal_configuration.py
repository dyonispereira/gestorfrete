from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.fiscal_configuration_dto import FiscalConfigurationDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetFiscalConfigurationQuery(Query):
    actor: AuthenticatedActor


class GetFiscalConfigurationHandler(QueryHandler[GetFiscalConfigurationQuery, FiscalConfigurationDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetFiscalConfigurationQuery) -> FiscalConfigurationDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyFiscalConfigurationRepository(session)
            config = await repo.get_for_tenant()
        if config is None:
            raise NotFoundError("FISCAL_CONFIG_NOT_FOUND", "Configuração Fiscal do tenant não encontrada.")
        return FiscalConfigurationDTO.from_entity(config)
