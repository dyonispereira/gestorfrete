from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOrdensServicoQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    veiculo_tracionador_id: uuid.UUID | None = None
    tipo: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListOrdensServicoResult:
    items: list[OrdemServicoDTO]
    total: int


class ListOrdensServicoHandler(QueryHandler[ListOrdensServicoQuery, ListOrdensServicoResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOrdensServicoQuery) -> ListOrdensServicoResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyOrdemServicoRepository(session)
            ordens, total = await repo.list_page(
                page=query.page, limit=query.limit, veiculo_tracionador_id=query.veiculo_tracionador_id,
                tipo=query.tipo, status=query.status,
            )
        return ListOrdensServicoResult(items=[OrdemServicoDTO.from_entity(o) for o in ordens], total=total)
