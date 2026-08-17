from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.documents.domain.entities.mdfe import Mdfe
from shared_kernel.domain.repository import Repository


class MdfeRepository(Repository[Mdfe, uuid.UUID]):
    @abstractmethod
    async def get_by_protocolo_sefaz(self, protocolo_sefaz: str) -> Mdfe | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, status: str | None, serie: str | None,
    ) -> tuple[list[Mdfe], int]: ...

    @abstractmethod
    async def add_cte_link(self, mdfe_id: uuid.UUID, cte_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_cte_ids(self, mdfe_id: uuid.UUID) -> list[uuid.UUID]: ...
