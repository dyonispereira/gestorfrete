from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.crm.domain.entities.client_contact import ClientContact


class ClientContactRepository(ABC):
    """Não herda `Repository[...]` (`shared_kernel`) porque `ClientContact` não é um Aggregate Root
    (`BaseEntity`, não `BaseAggregateRoot`) — mesma razão de `PermissionRepository` no Lote 2 não
    herdar a interface genérica de Aggregate Root."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ClientContact | None: ...

    @abstractmethod
    async def list_for_client(self, cliente_id: uuid.UUID) -> list[ClientContact]: ...

    @abstractmethod
    async def add(self, contact: ClientContact) -> None: ...
