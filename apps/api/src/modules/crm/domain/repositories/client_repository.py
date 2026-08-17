from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.crm.domain.entities.client import Client
from shared_kernel.domain.repository import Repository


class ClientRepository(Repository[Client, uuid.UUID]):
    @abstractmethod
    async def exists_with_document(self, document: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        document: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Client], int]: ...
