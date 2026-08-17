from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.drivers.domain.entities.driver_document import DriverDocument


class DriverDocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> DriverDocument | None: ...

    @abstractmethod
    async def list_for_driver(self, motorista_id: uuid.UUID) -> list[DriverDocument]: ...

    @abstractmethod
    async def add(self, document: DriverDocument) -> None: ...

    @abstractmethod
    async def delete(self, document: DriverDocument) -> None: ...
