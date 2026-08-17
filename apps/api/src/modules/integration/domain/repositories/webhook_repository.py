from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.integration.domain.entities.webhook import Webhook


class WebhookRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Webhook | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, integration_config_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[Webhook], int]: ...

    @abstractmethod
    async def add(self, webhook: Webhook) -> None: ...
