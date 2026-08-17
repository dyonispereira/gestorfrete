from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.fleet.domain.entities.vehicle_availability import VehicleAvailability
from modules.fleet.domain.value_objects.availability_status import AvailabilityStatus


class VehicleAvailabilityRepository(ABC):
    """Deliberadamente menor que `Repository[...]` genérico — só leitura pública + `apply(...)`,
    a única forma de escrever nesta tabela em todo o código (D247,
    `AVAILABILITY_IMPLEMENTATION.md`). Nenhum Command/Router chama `apply(...)` — só
    `VehicleAvailabilityProjector`."""

    @abstractmethod
    async def get_by_vehicle_id(self, veiculo_tracionador_id: uuid.UUID) -> VehicleAvailability | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None
    ) -> tuple[list[VehicleAvailability], int]: ...

    @abstractmethod
    async def apply(
        self,
        *,
        veiculo_tracionador_id: uuid.UUID,
        status: AvailabilityStatus,
        motorista_atual_id: uuid.UUID | None,
        implemento_atual_id: uuid.UUID | None,
        now: datetime,
    ) -> None: ...
