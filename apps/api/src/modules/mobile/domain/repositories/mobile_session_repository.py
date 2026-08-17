from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.mobile.domain.entities.mobile_session import MobileSession


class MobileSessionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> MobileSession | None: ...

    @abstractmethod
    async def add(self, session: MobileSession) -> None: ...
