from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import date

from modules.financial.domain.entities.accounts_payable import AccountsPayable
from shared_kernel.domain.repository import Repository


class AccountsPayableRepository(Repository[AccountsPayable, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        origin: str | None,
        supplier_id: uuid.UUID | None,
        cost_center_id: uuid.UUID | None,
        trip_id: uuid.UUID | None,
        vehicle_id: uuid.UUID | None,
        chart_of_accounts_id: uuid.UUID | None,
        accounting_period: date | None,
        due_date_from: date | None,
        due_date_to: date | None,
    ) -> tuple[list[AccountsPayable], int]: ...

    @abstractmethod
    async def exists_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> bool:
        """Idempotência da Conta a Pagar automática (`OrdemServicoFechada` → Conta a Pagar, Lote
        Financeiro Parte 1) — a mesma OS nunca gera duas, mesmo se `FECHADA` for reprocessada."""
        ...
