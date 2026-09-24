from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.collection import Collection


class CollectionRepository(ABC):
    """`coletas` — não é um Aggregate Root próprio, filho do agregado Viagem (mesmo padrão de
    `OccurrenceRepository`/`ProofOfDeliveryRepository`)."""

    @abstractmethod
    async def exists_for_trip(self, viagem_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def create(self, collection: Collection) -> None: ...
