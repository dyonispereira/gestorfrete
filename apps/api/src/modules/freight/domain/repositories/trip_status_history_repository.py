from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension


class TripStatusHistoryRepository(ABC):
    """`viagem_status_history` — append-only (D017/D018), particionada por mês. Nunca um
    `Repository[...]` genérico: não há `get_by_id` isolado com sentido de negócio, só consultas por
    Viagem."""

    @abstractmethod
    async def add(self, entry: TripStatusHistoryEntry) -> None: ...

    @abstractmethod
    async def get_last_operational_before(self, viagem_id: uuid.UUID, before: datetime) -> TripStatusHistoryEntry | None:
        """D377 — resolve o estado de origem para `commands/retomar`."""
        ...

    @abstractmethod
    async def exists_accepted(self, viagem_id: uuid.UUID) -> bool:
        """D379 — idempotência de `commands/accept`."""
        ...

    @abstractmethod
    async def list_for_trip_cursor(
        self,
        viagem_id: uuid.UUID,
        *,
        dimensao: StatusHistoryDimension | None,
        limit: int,
        after_data_hora: datetime | None,
        after_id: uuid.UUID | None,
    ) -> list[TripStatusHistoryEntry]: ...
