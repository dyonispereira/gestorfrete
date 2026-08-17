from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.application.queries.get_delivery import GetDeliveryHandler, GetDeliveryQuery
from modules.mobile.application.queries.ownership import assert_owns_trip
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetOwnDeliveryQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    trip_id: uuid.UUID
    delivery_id: uuid.UUID


class GetOwnDeliveryHandler(QueryHandler[GetOwnDeliveryQuery, DeliveryDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetOwnDeliveryQuery) -> DeliveryDTO:
        await assert_owns_trip(
            self._session_factory, actor=query.actor, driver_id=query.driver_id, trip_id=query.trip_id
        )
        return await GetDeliveryHandler(self._session_factory).handle(
            GetDeliveryQuery(actor=query.actor, trip_id=query.trip_id, delivery_id=query.delivery_id)
        )
