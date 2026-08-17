from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.fleet.domain.entities.vehicle_composition import VehicleComposition


class VehicleCompositionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> VehicleComposition | None: ...

    @abstractmethod
    async def get_current_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> VehicleComposition | None:
        """Composição com `data_fim_vigencia IS NULL` para o veículo — no máximo uma
        (`uq_composicoes_veiculares_vigente`)."""

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, veiculo_tracionador_id: uuid.UUID | None, tipo_combinacao: str | None, vigente: bool
    ) -> tuple[list[VehicleComposition], int]: ...

    @abstractmethod
    async def add(self, composition: VehicleComposition) -> None: ...

    @abstractmethod
    async def count_active_for_implement(self, implement_id: uuid.UUID) -> int:
        """Suporta `FLEET_IMPLEMENT_IN_COMPOSITION` (`IMPLEMENT_IMPLEMENTATION.md`)."""
