from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.tracking.domain.entities.tracking_equipment import TrackingEquipment


class TrackingEquipmentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> TrackingEquipment | None: ...

    @abstractmethod
    async def get_by_serial(self, identificador_serial: str) -> TrackingEquipment | None: ...

    @abstractmethod
    async def get_principal_vigente(self, veiculo_tracionador_id: uuid.UUID) -> TrackingEquipment | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, vehicle_id: uuid.UUID | None, provider_id: uuid.UUID | None,
        equipment_type: str | None, status: str | None,
    ) -> tuple[list[TrackingEquipment], int]: ...

    @abstractmethod
    async def add(self, equipment: TrackingEquipment) -> None: ...
