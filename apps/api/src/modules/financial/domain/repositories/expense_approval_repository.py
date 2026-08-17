from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.expense_approval import ExpenseApproval


class ExpenseApprovalRepository(ABC):
    @abstractmethod
    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[ExpenseApproval]: ...

    @abstractmethod
    async def add(self, approval: ExpenseApproval) -> None: ...
