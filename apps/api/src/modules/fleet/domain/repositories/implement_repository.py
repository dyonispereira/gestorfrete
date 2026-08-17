from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.fleet.domain.entities.implement import Implement


class ImplementRepository(ABC):
    """Não herda `Repository[...]` genérico — `Implement` não tem `_por` de auditoria e nunca usa
    `Specification` (mesma razão de `ClientContactRepository`, Lote 3)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Implement | None: ...

    @abstractmethod
    async def exists_with_placa(self, placa: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, tipo_carroceria: str | None, status: str | None
    ) -> tuple[list[Implement], int]: ...

    @abstractmethod
    async def add(self, implement: Implement) -> None: ...

    @abstractmethod
    async def exists_in_active_composition(self, implement_id: uuid.UUID) -> bool:
        """Suporta `FLEET_IMPLEMENT_IN_COMPOSITION` (`IMPLEMENT_IMPLEMENTATION.md`)."""
