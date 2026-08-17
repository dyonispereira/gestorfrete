from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListDeliveriesQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class ListDeliveriesHandler(QueryHandler[ListDeliveriesQuery, list[DeliveryDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListDeliveriesQuery) -> list[DeliveryDTO]:
        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            if await trip_repo.get_by_id(query.trip_id) is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            delivery_repo = SqlAlchemyDeliveryRepository(session)
            deliveries = await delivery_repo.list_for_trip(query.trip_id)
            result = []
            for delivery in deliveries:
                window = await delivery_repo.get_window(delivery.id)
                result.append(DeliveryDTO.from_entity(delivery, window))
        return result
