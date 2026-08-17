from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.crm.application.dtos.client_dto import ClientDTO
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListClientsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    document: str | None = None
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


@dataclass(frozen=True)
class ListClientsResult:
    items: list[ClientDTO]
    total: int


class ListClientsHandler(QueryHandler[ListClientsQuery, ListClientsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListClientsQuery) -> ListClientsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyClientRepository(session)
            clients, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                status=query.status,
                document=query.document,
                search=query.search,
                created_from=query.created_from,
                created_to=query.created_to,
            )
        return ListClientsResult(items=[ClientDTO.from_entity(c) for c in clients], total=total)
