from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.documents.domain.entities.ciot import Ciot
from shared_kernel.domain.repository import Repository


class CiotRepository(Repository[Ciot, uuid.UUID]):
    @abstractmethod
    async def get_by_protocolo_antt(self, protocolo_antt: str) -> Ciot | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, motorista_id: uuid.UUID | None,
        status: str | None,
    ) -> tuple[list[Ciot], int]: ...
