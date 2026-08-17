from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.maintenance.domain.entities.supplier import Supplier
from shared_kernel.domain.repository import Repository


class SupplierRepository(Repository[Supplier, uuid.UUID]):
    @abstractmethod
    async def exists_with_cnpj(self, cnpj: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        category: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Supplier], int]: ...
