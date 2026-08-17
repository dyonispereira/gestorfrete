from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.proof_of_delivery import ProofOfDelivery


class ProofOfDeliveryRepository(ABC):
    @abstractmethod
    async def get_for_delivery(self, entrega_id: uuid.UUID) -> ProofOfDelivery | None: ...

    @abstractmethod
    async def exists_for_delivery(self, entrega_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def create(self, proof_of_delivery: ProofOfDelivery) -> None: ...
