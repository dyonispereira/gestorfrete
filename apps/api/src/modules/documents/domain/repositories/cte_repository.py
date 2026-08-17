from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.documents.domain.entities.cte import Cte
from shared_kernel.domain.repository import Repository


class CteRepository(Repository[Cte, uuid.UUID]):
    @abstractmethod
    async def get_by_protocolo_sefaz(self, protocolo_sefaz: str) -> Cte | None: ...

    @abstractmethod
    async def list_authorized_for_trip(self, viagem_id: uuid.UUID) -> list[Cte]: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, status: str | None,
        serie: str | None, chave_acesso: str | None,
    ) -> tuple[list[Cte], int]: ...
