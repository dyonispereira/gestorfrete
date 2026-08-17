from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.tracking.domain.entities.speed_limit_config import SpeedLimitConfig


class SpeedLimitConfigRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> SpeedLimitConfig | None: ...

    @abstractmethod
    async def get_applicable(self, categoria_veiculo_id: uuid.UUID | None) -> SpeedLimitConfig | None:
        """Resolve a configuração aplicável: pela categoria do veículo se existir uma `ATIVA`, senão
        o padrão do tenant (`categoria_veiculo_id IS NULL`)."""
        ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, vehicle_category_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[SpeedLimitConfig], int]: ...

    @abstractmethod
    async def add(self, config: SpeedLimitConfig) -> None: ...
