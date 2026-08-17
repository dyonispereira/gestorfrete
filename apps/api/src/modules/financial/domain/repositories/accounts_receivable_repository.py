from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from decimal import Decimal

from modules.financial.domain.entities.accounts_receivable import AccountsReceivable


class AccountsReceivableRepository(ABC):
    """Sub-recurso de `Invoice` — não é um Aggregate Root próprio, sem `Repository[...]`
    genérico (mesmo padrão de `DeliveryRepository`, Lote 5)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AccountsReceivable | None: ...

    @abstractmethod
    async def add(self, receivable: AccountsReceivable) -> None: ...

    @abstractmethod
    async def list_for_invoice(self, fatura_id: uuid.UUID) -> list[AccountsReceivable]: ...

    @abstractmethod
    async def exists_with_installment(self, fatura_id: uuid.UUID, numero_parcela: int) -> bool: ...

    @abstractmethod
    async def count_pending_for_invoice(self, fatura_id: uuid.UUID, *, excluding_id: uuid.UUID | None = None) -> int: ...

    @abstractmethod
    async def sum_received_for_invoice(self, fatura_id: uuid.UUID) -> Decimal: ...
