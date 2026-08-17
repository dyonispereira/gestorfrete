from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.fleet.domain.entities.vehicle_document import VehicleDocument


class VehicleDocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> VehicleDocument | None: ...

    @abstractmethod
    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, page: int, limit: int, tipo: str | None, status: str | None
    ) -> tuple[list[VehicleDocument], int]: ...

    @abstractmethod
    async def add(self, document: VehicleDocument) -> None: ...
