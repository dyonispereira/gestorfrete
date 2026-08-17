from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.financial.domain.entities.invoice import Invoice
from shared_kernel.domain.repository import Repository


class InvoiceRepository(Repository[Invoice, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, client_id: uuid.UUID | None, status: str | None, trip_id: uuid.UUID | None
    ) -> tuple[list[Invoice], int]: ...

    @abstractmethod
    async def exists_with_numero(self, numero_fatura: str) -> bool: ...
