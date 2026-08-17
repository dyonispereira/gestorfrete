from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from shared.addresses.application.dtos.address_dto import AddressDTO
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SqlAlchemyAddressRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAddressQuery(Query):
    actor: AuthenticatedActor
    owner_type: OwnerType
    owner_id: uuid.UUID
    address_id: uuid.UUID


class GetAddressHandler(QueryHandler[GetAddressQuery, AddressDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAddressQuery) -> AddressDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAddressRepository(session)
            address = await repo.get_by_id(query.address_id)
        if address is None or address.owner_type != query.owner_type or address.owner_id != query.owner_id:
            raise NotFoundError("ADDRESS_NOT_FOUND", "Endereço não encontrado.")
        return AddressDTO.from_entity(address)
