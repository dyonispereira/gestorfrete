from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.fleet.domain.entities.odometer_reading import OdometerReading


class OdometerReadingRepository(ABC):
    @abstractmethod
    async def get_latest_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> OdometerReading | None:
        """Suporta o invariante "nunca decresce" (D365)."""

    @abstractmethod
    async def list_for_vehicle_cursor(
        self,
        *,
        veiculo_tracionador_id: uuid.UUID,
        limit: int,
        origem: str | None,
        after_data_hora: datetime | None,
        after_id: uuid.UUID | None,
    ) -> list[OdometerReading]:
        """`after_data_hora`/`after_id` decodificados do cursor opaco (`PAGINATION.md`)."""

    @abstractmethod
    async def add(self, reading: OdometerReading) -> None: ...
