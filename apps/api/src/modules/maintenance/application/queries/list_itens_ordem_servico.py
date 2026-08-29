from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.item_ordem_servico_dto import ItemOrdemServicoDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_item_ordem_servico_repository import (
    SqlAlchemyItemOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListItensOrdemServicoQuery(Query):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID


class ListItensOrdemServicoHandler(QueryHandler[ListItensOrdemServicoQuery, list[ItemOrdemServicoDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListItensOrdemServicoQuery) -> list[ItemOrdemServicoDTO]:
        async with self._session_factory() as session:
            os_repo = SqlAlchemyOrdemServicoRepository(session)
            if await os_repo.get_by_id(query.ordem_servico_id) is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            item_repo = SqlAlchemyItemOrdemServicoRepository(session)
            itens = await item_repo.list_for_ordem_servico(query.ordem_servico_id)
        return [ItemOrdemServicoDTO.from_entity(i) for i in itens]
