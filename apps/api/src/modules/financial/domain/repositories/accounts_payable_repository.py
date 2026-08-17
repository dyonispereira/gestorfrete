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
        due_date_from: date | None,
        due_date_to: date | None,
    ) -> tuple[list[AccountsPayable], int]: ...
