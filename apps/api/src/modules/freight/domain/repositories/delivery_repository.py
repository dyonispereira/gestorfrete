from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.delivery import Delivery
from modules.freight.domain.entities.delivery_window import DeliveryWindow


class DeliveryRepository(ABC):
    """`entregas` — não é um Aggregate Root próprio (D232, filho de `Trip`), sem `Repository[...]`
    genérico (mesmo padrão de `VehicleDocumentRepository`, Lote 4)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Delivery | None: ...

    @abstractmethod
    async def add(self, aggregate: Delivery) -> None: ...

    @abstractmethod
    async def list_for_trip(self, viagem_id: uuid.UUID) -> list[Delivery]: ...

    @abstractmethod
    async def exists_with_order(self, viagem_id: uuid.UUID, ordem: int) -> bool: ...

    @abstractmethod
    async def count_pending_for_trip(self, viagem_id: uuid.UUID, *, excluding_id: uuid.UUID | None = None) -> int: ...

    @abstractmethod
    async def get_window(self, entrega_id: uuid.UUID) -> DeliveryWindow | None: ...

    @abstractmethod
    async def add_window(self, window: DeliveryWindow) -> None: ...
