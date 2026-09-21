from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.financial.domain.entities.invoice_trip import InvoiceTrip


class InvoiceTripRepository(ABC):
    """Sub-recurso de `Invoice` — não é um Aggregate Root próprio, mesmo padrão de
    `AccountsReceivableRepository` (Lote Financeiro, Parte 3)."""

    @abstractmethod
    async def add(self, invoice_trip: InvoiceTrip) -> None: ...

    @abstractmethod
    async def list_for_invoice(self, fatura_id: uuid.UUID) -> list[InvoiceTrip]: ...

    @abstractmethod
    async def list_for_invoices_batch(self, fatura_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[InvoiceTrip]]:
        """Evita N+1 numa listagem paginada de Faturas — uma query para todas da página."""
        ...

    @abstractmethod
    async def exists_active_for_trip(self, viagem_id: uuid.UUID) -> bool:
        """Uma Viagem já vinculada a uma Fatura não `CANCELADA` não pode ser incluída novamente
        (invariante entre agregados, checada na aplicação — `CANCELADA` é join com `faturas`)."""
        ...
