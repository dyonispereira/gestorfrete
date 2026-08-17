from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.addresses.application.dtos.address_dto import AddressDTO
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SqlAlchemyAddressRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAddressesQuery(Query):
    actor: AuthenticatedActor
    owner_type: OwnerType
    owner_id: uuid.UUID


class ListAddressesHandler(QueryHandler[ListAddressesQuery, list[AddressDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAddressesQuery) -> list[AddressDTO]:
        async with self._session_factory() as session:
            repo = SqlAlchemyAddressRepository(session)
            addresses = await repo.list_for_owner(query.owner_type, query.owner_id)
        return [AddressDTO.from_entity(a) for a in addresses]
