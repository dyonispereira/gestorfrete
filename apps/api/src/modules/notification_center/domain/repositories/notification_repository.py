from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.notification_center.domain.entities.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Notification | None: ...

    @abstractmethod
    async def list_page_for_user(
        self, usuario_id: uuid.UUID, *, page: int, limit: int, channel: str | None, status: str | None
    ) -> tuple[list[Notification], int]: ...

    @abstractmethod
    async def add(self, notification: Notification) -> None: ...
