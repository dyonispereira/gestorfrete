from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.tracking.domain.entities.location_origin import LocationOrigin


class LocationOriginRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> LocationOrigin | None: ...

    @abstractmethod
    async def get_by_nome(self, nome: str) -> LocationOrigin | None: ...

    @abstractmethod
    async def list_page(self, *, page: int, limit: int) -> tuple[list[LocationOrigin], int]: ...

    @abstractmethod
    async def add(self, origin: LocationOrigin) -> None:
        """Só usado pelo seed (D406) — nenhum comando de aplicação expõe criação via HTTP."""
        ...
