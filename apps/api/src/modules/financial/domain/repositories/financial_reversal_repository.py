from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.financial_reversal import FinancialReversal


class FinancialReversalRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> FinancialReversal | None: ...

    @abstractmethod
    async def add(self, reversal: FinancialReversal) -> None: ...

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        invoice_id: uuid.UUID | None,
        accounts_payable_id: uuid.UUID | None,
        accounts_receivable_id: uuid.UUID | None,
    ) -> tuple[list[FinancialReversal], int]: ...
