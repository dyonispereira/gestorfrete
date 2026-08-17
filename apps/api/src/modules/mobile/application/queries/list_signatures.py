from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.mobile.application.dtos.digital_signature_dto import DigitalSignatureDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_digital_signature_repository import (
    SqlAlchemyDigitalSignatureRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSignaturesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    document_type: str | None = None
    document_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ListSignaturesResult:
    items: list[DigitalSignatureDTO]
    total: int


class ListSignaturesHandler(QueryHandler[ListSignaturesQuery, ListSignaturesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSignaturesQuery) -> ListSignaturesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyDigitalSignatureRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, document_type=query.document_type, document_id=query.document_id
            )
        return ListSignaturesResult(items=[DigitalSignatureDTO.from_entity(s) for s in items], total=total)
