from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.tracking.domain.entities.tracking_provider import TrackingProvider


class TrackingProviderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> TrackingProvider | None: ...

    @abstractmethod
    async def get_by_nome(self, nome: str) -> TrackingProvider | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, status: str | None
    ) -> tuple[list[TrackingProvider], int]: ...

    @abstractmethod
    async def add(self, provider: TrackingProvider) -> None: ...
