from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.notification_center.domain.entities.channel_preference import ChannelPreference
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel


class ChannelPreferenceRepository(ABC):
    @abstractmethod
    async def get(self, usuario_id: uuid.UUID, canal: NotificationChannel) -> ChannelPreference | None: ...

    @abstractmethod
    async def list_for_user(self, usuario_id: uuid.UUID) -> list[ChannelPreference]: ...

    @abstractmethod
    async def add(self, preference: ChannelPreference) -> None: ...
