from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.payment_method import PaymentMethod


class PaymentMethodRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> PaymentMethod | None: ...

    @abstractmethod
    async def add(self, payment_method: PaymentMethod) -> None: ...
