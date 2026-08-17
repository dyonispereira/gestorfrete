from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.documents.domain.entities.referenced_nfe import ReferencedNfe


class ReferencedNfeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ReferencedNfe | None: ...

    @abstractmethod
    async def add(self, nfe: ReferencedNfe) -> None: ...

    @abstractmethod
    async def list_for_cte(self, cte_id: uuid.UUID) -> list[ReferencedNfe]: ...
