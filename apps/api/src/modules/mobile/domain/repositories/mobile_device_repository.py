from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.mobile.domain.entities.mobile_device import MobileDevice


class MobileDeviceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> MobileDevice | None: ...

    @abstractmethod
    async def get_by_identifier(self, identificador_dispositivo: str) -> MobileDevice | None:
        """Único globalmente (D084) — sem filtro de tenant, dado físico do aparelho."""
        ...

    @abstractmethod
    async def list_page(
        self, *, motorista_id: uuid.UUID, page: int, limit: int
    ) -> tuple[list[MobileDevice], int]: ...

    @abstractmethod
    async def add(self, device: MobileDevice) -> None: ...
