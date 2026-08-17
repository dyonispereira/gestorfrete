from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.tracking.domain.entities.telemetry_reading import TelemetryReading


class TelemetryReadingRepository(ABC):
    @abstractmethod
    async def add(self, reading: TelemetryReading) -> None: ...

    @abstractmethod
    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, after_capturado_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, sensor_type: str | None,
        captured_at_gte: datetime | None, captured_at_lte: datetime | None, equipment_id: uuid.UUID | None,
    ) -> list[TelemetryReading]: ...
