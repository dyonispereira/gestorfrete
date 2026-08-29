from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetOrdemServicoQuery(Query):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID


class GetOrdemServicoHandler(QueryHandler[GetOrdemServicoQuery, OrdemServicoDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetOrdemServicoQuery) -> OrdemServicoDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyOrdemServicoRepository(session)
            ordem_servico = await repo.get_by_id(query.ordem_servico_id)
        if ordem_servico is None:
            raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")
        return OrdemServicoDTO.from_entity(ordem_servico)
