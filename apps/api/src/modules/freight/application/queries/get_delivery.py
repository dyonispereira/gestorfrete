from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetDeliveryQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    delivery_id: uuid.UUID


class GetDeliveryHandler(QueryHandler[GetDeliveryQuery, DeliveryDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetDeliveryQuery) -> DeliveryDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDeliveryRepository(session)
            delivery = await repo.get_by_id(query.delivery_id)
            if delivery is None or delivery.viagem_id != query.trip_id:
                raise NotFoundError("FREIGHT_DELIVERY_NOT_FOUND", "Entrega não encontrada.")
            window = await repo.get_window(delivery.id)
        return DeliveryDTO.from_entity(delivery, window)
