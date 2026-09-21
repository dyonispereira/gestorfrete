from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date
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

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        client_id: uuid.UUID | None,
        accounting_period: date | None,
        due_date_from: date | None,
        due_date_to: date | None,
    ) -> tuple[list[tuple[AccountsReceivable, uuid.UUID]], int]:
        """Consulta agregada entre Faturas (Lote Financeiro, Parte 2.1) — "o que tenho para
        receber hoje" sem precisar abrir Fatura por Fatura. Ownership não muda (Conta a Receber
        continua sub-recurso de Fatura, D260) — isto é só uma superfície de leitura própria, por
        isso devolve `(AccountsReceivable, cliente_id)`: `cliente_id` nunca vira campo do
        agregado, só um dado de leitura obtido via join com `faturas` para esta consulta."""
        ...
