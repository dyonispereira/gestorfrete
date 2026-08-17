from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.integration.domain.entities.integration_config import IntegrationConfig


class IntegrationConfigRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> IntegrationConfig | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, tipo: str | None, status: str | None
    ) -> tuple[list[IntegrationConfig], int]: ...

    @abstractmethod
    async def add(self, config: IntegrationConfig) -> None: ...
