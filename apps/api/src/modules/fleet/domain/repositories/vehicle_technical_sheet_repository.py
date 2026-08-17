from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.fleet.domain.entities.vehicle_technical_sheet import VehicleTechnicalSheet


class VehicleTechnicalSheetRepository(ABC):
    @abstractmethod
    async def get_by_vehicle_id(self, veiculo_tracionador_id: uuid.UUID) -> VehicleTechnicalSheet | None: ...

    @abstractmethod
    async def exists_with_chassi(self, chassi: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def add(self, sheet: VehicleTechnicalSheet) -> None: ...
