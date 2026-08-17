from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.financial.domain.entities.cost_center import CostCenter
from shared_kernel.domain.repository import Repository


class CostCenterRepository(Repository[CostCenter, uuid.UUID]):
    @abstractmethod
    async def exists_with_codigo_contabil(self, codigo_contabil: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None, branch_id: uuid.UUID | None, search: str | None
    ) -> tuple[list[CostCenter], int]: ...
