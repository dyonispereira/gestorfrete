from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.mobile.application.dtos.mobile_device_dto import MobileDeviceDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_device_repository import (
    SqlAlchemyMobileDeviceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetMobileDeviceQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    device_id: uuid.UUID


class GetMobileDeviceHandler(QueryHandler[GetMobileDeviceQuery, MobileDeviceDTO]):
    """`061-driver-devices.md` — `403` quando o dispositivo não pertence ao Motorista da sessão."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetMobileDeviceQuery) -> MobileDeviceDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyMobileDeviceRepository(session)
            device = await repo.get_by_id(query.device_id)
        if device is None:
            raise NotFoundError("MOBILE_DEVICE_NOT_FOUND", "Dispositivo não encontrado.")
        if device.motorista_id != query.driver_id:
            raise AuthorizationError("MOBILE_DEVICE_FORBIDDEN", "Dispositivo não pertence ao Motorista da sessão.")
        return MobileDeviceDTO.from_entity(device)
