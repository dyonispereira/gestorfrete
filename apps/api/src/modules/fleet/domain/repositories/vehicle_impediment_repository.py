from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.fleet.domain.entities.vehicle_impediment import VehicleImpediment
from modules.fleet.domain.value_objects.impediment_type import ImpedimentoTipo


class VehicleImpedimentRepository(ABC):
    """Escrita restrita a `VehicleAvailabilityProjector` (mesmo princípio de D247 aplicado ao
    ledger que agora sustenta `disponibilidade_veiculo`)."""

    @abstractmethod
    async def get_active(
        self, *, veiculo_tracionador_id: uuid.UUID, tipo: ImpedimentoTipo, referencia_id: uuid.UUID
    ) -> VehicleImpediment | None: ...

    @abstractmethod
    async def list_active(self, veiculo_tracionador_id: uuid.UUID) -> list[VehicleImpediment]: ...

    @abstractmethod
    async def add(self, impediment: VehicleImpediment) -> None: ...

    @abstractmethod
    async def close(
        self, *, veiculo_tracionador_id: uuid.UUID, tipo: ImpedimentoTipo, referencia_id: uuid.UUID, now: datetime
    ) -> None:
        """Idempotente — se não houver impedimento ativo casando `tipo`+`referencia_id`, não faz
        nada (retry-safe, mesma característica dos comandos de transição de status)."""
        ...
