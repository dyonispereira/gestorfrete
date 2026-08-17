from __future__ import annotations

import uuid
from abc import abstractmethod
from decimal import Decimal

from modules.financial.domain.entities.bank_account import BankAccount
from shared_kernel.domain.repository import Repository


class BankAccountRepository(Repository[BankAccount, uuid.UUID]):
    @abstractmethod
    async def exists_with_numero_conta(self, numero_conta: str) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None, tipo: str | None
    ) -> tuple[list[BankAccount], int]: ...

    @abstractmethod
    async def calculate_tenant_balance(self) -> Decimal:
        """D263/D394 — saldo sempre derivado; agregado do tenant inteiro (sem coluna
        `conta_bancaria_id` em `contas_pagar`/`contas_receber`, D394)."""
        ...
