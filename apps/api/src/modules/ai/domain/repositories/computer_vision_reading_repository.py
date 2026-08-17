from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.computer_vision_reading import ComputerVisionReading


class ComputerVisionReadingRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ComputerVisionReading | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, tipo_leitura: str | None, status: str | None,
        revisao_humana_necessaria: bool | None,
    ) -> tuple[list[ComputerVisionReading], int]: ...

    @abstractmethod
    async def add(self, reading: ComputerVisionReading) -> None: ...
