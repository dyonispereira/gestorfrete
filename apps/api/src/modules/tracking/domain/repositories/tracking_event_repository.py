from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.tracking.domain.entities.tracking_event import TrackingEvent


class TrackingEventRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> TrackingEvent | None: ...

    @abstractmethod
    async def add(self, event: TrackingEvent) -> None: ...

    @abstractmethod
    async def exists_referencing_geofence(self, cerca_eletronica_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, after_data_hora: datetime | None, after_id: uuid.UUID | None, limit: int,
        types: list[str] | None, severity: str | None, vehicle_id: uuid.UUID | None,
        occurred_at_gte: datetime | None, occurred_at_lte: datetime | None,
    ) -> list[TrackingEvent]:
        """`types` — quando `None`, o chamador (Application) já resolveu a lista de categorias
        permitidas para o Actor (D294, filtragem por linha); nunca `None` significa "todas sem
        checar"."""
        ...
