from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.trip_allocation import TripAllocation


class TripAllocationRepository(ABC):
    """`alocacoes_recurso_viagem` — não é um Aggregate Root próprio (D188, filho de `Trip`), sem
    `Repository[...]` genérico: nunca `get_by_id` isolado sem o contexto da Viagem."""

    @abstractmethod
    async def get_current_for_trip(self, viagem_id: uuid.UUID) -> TripAllocation | None: ...

    @abstractmethod
    async def list_for_trip(self, viagem_id: uuid.UUID, *, include_superseded: bool) -> list[TripAllocation]: ...

    @abstractmethod
    async def exists_vigente_for_vehicle_excluding_trip(self, veiculo_tracionador_id: uuid.UUID, viagem_id: uuid.UUID) -> bool:
        """`FREIGHT_VEHICLE_UNAVAILABLE` (`016-trip-resources.md`) — Veículo já alocado como
        `VIGENTE` em **outra** Viagem."""
        ...

    @abstractmethod
    async def add(self, allocation: TripAllocation) -> None: ...
