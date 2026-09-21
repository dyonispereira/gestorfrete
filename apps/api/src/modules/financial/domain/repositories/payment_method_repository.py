from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.payment_method import PaymentMethod


class PaymentMethodRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> PaymentMethod | None: ...

    @abstractmethod
    async def add(self, payment_method: PaymentMethod) -> None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None
    ) -> tuple[list[PaymentMethod], int]: ...

    @abstractmethod
    async def exists_with_nome(self, nome: str) -> bool: ...
