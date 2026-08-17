from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.tracking.domain.entities.vehicle_position import VehiclePosition


class VehiclePositionRepository(ABC):
    @abstractmethod
    async def add(self, position: VehiclePosition) -> None: ...

    @abstractmethod
    async def get_latest_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> VehiclePosition | None:
        """A posição mais recente do veículo — usada por `TrackingIngestion` para saber o estado
        anterior de contenção de geofence antes de decidir se a posição nova é uma transição."""
        ...

    @abstractmethod
    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, after_capturado_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, captured_at_gte: datetime | None,
        captured_at_lte: datetime | None, origin_id: uuid.UUID | None, equipment_id: uuid.UUID | None,
    ) -> list[VehiclePosition]: ...
