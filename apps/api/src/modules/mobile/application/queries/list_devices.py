from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.mobile.application.dtos.mobile_device_dto import MobileDeviceDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_device_repository import (
    SqlAlchemyMobileDeviceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListMobileDevicesQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ListMobileDevicesResult:
    items: list[MobileDeviceDTO]
    total: int


class ListMobileDevicesHandler(QueryHandler[ListMobileDevicesQuery, ListMobileDevicesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListMobileDevicesQuery) -> ListMobileDevicesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyMobileDeviceRepository(session)
            items, total = await repo.list_page(motorista_id=query.driver_id, page=query.page, limit=query.limit)
        return ListMobileDevicesResult(items=[MobileDeviceDTO.from_entity(d) for d in items], total=total)
