from __future__ import annotations

import uuid
from abc import abstractmethod

from shared.addresses.domain.entities.address import Address
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared_kernel.domain.repository import Repository


class AddressRepository(Repository[Address, uuid.UUID]):
    """Injetada por qualquer módulo dono (`crm`/`maintenance`, futuramente `tenancy`) — nunca
    reimplementada internamente (D354)."""

    @abstractmethod
    async def list_for_owner(self, owner_type: OwnerType, owner_id: uuid.UUID) -> list[Address]: ...

    @abstractmethod
    async def has_principal(self, owner_type: OwnerType, owner_id: uuid.UUID) -> bool: ...
