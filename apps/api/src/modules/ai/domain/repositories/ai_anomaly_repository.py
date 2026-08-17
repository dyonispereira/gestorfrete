from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_anomaly import AIAnomaly


class AIAnomalyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIAnomaly | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, leitura_origem_tipo: str | None, status: str | None,
    ) -> tuple[list[AIAnomaly], int]: ...

    @abstractmethod
    async def add(self, anomaly: AIAnomaly) -> None: ...
