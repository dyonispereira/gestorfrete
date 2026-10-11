from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.trip_price_application import TripPriceApplication


class TripPriceApplicationRepository(ABC):
    """Não estende `Repository[T, TId]` genérico (como os outros repositórios) porque
    `TripPriceApplication` é append-only (D109-consistent) — não há `add()` que sobrescreve por
    `id`, só `create()` (sempre uma linha nova) e `get_active_for_trip()`."""

    @abstractmethod
    async def create(self, application: TripPriceApplication) -> None: ...

    @abstractmethod
    async def get_active_for_trip(self, viagem_id: uuid.UUID) -> TripPriceApplication | None: ...

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> TripPriceApplication | None: ...

    @abstractmethod
    async def mark_removed(self, application: TripPriceApplication) -> None: ...
