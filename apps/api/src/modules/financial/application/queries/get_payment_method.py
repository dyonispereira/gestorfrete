from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.payment_method_dto import PaymentMethodDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetPaymentMethodQuery(Query):
    actor: AuthenticatedActor
    payment_method_id: uuid.UUID


class GetPaymentMethodHandler(QueryHandler[GetPaymentMethodQuery, PaymentMethodDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetPaymentMethodQuery) -> PaymentMethodDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyPaymentMethodRepository(session)
            payment_method = await repo.get_by_id(query.payment_method_id)
        if payment_method is None:
            raise NotFoundError("FINANCIAL_PAYMENT_METHOD_NOT_FOUND", "Forma de Pagamento não encontrada.")
        return PaymentMethodDTO.from_entity(payment_method)
