from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.fleet.domain.entities.vehicle_category import VehicleCategory


class VehicleCategoryRepository(ABC):
    """Sem `find`/`Specification` (não herda `Repository[...]` genérico) — uso interno mínimo,
    D363."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> VehicleCategory | None: ...

    @abstractmethod
    async def add(self, category: VehicleCategory) -> None: ...
