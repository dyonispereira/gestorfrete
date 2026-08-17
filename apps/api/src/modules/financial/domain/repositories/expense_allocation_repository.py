from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from decimal import Decimal

from modules.financial.domain.entities.expense_allocation import ExpenseAllocation


class ExpenseAllocationRepository(ABC):
    @abstractmethod
    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[ExpenseAllocation]: ...

    @abstractmethod
    async def add(self, allocation: ExpenseAllocation) -> None: ...

    @abstractmethod
    async def delete_for_payable(self, conta_pagar_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def sum_for_trip(self, viagem_id: uuid.UUID) -> Decimal:
        """Alimenta `Trip.custo_realizado` via `TripInternalTransitions` (D390)."""
        ...
