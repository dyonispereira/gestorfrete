from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.payment_method_dto import PaymentMethodDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListPaymentMethodsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None


@dataclass(frozen=True)
class ListPaymentMethodsResult:
    items: list[PaymentMethodDTO]
    total: int


class ListPaymentMethodsHandler(QueryHandler[ListPaymentMethodsQuery, ListPaymentMethodsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListPaymentMethodsQuery) -> ListPaymentMethodsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyPaymentMethodRepository(session)
            payment_methods, total = await repo.list_page(page=query.page, limit=query.limit, status=query.status)
        return ListPaymentMethodsResult(
            items=[PaymentMethodDTO.from_entity(p) for p in payment_methods], total=total
        )
