from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.mobile.domain.entities.sync_queue_item import SyncQueueItem


class SyncQueueItemRepository(ABC):
    @abstractmethod
    async def get_by_local_id(self, sessao_mobile_id: uuid.UUID, identificador_local_unico: str) -> SyncQueueItem | None: ...

    @abstractmethod
    async def add_if_absent(self, item: SyncQueueItem) -> SyncQueueItem:
        """D111 — `INSERT ... ON CONFLICT (sessao_mobile_id, identificador_local_unico) DO NOTHING`.
        Retorna a linha que passou a existir (a nova, ou a já existente em caso de reenvio) —
        chamador nunca precisa distinguir os dois casos manualmente."""
        ...

    @abstractmethod
    async def update(self, item: SyncQueueItem) -> None: ...

    @abstractmethod
    async def list_pending_ordered(self, sessao_mobile_id: uuid.UUID) -> list[SyncQueueItem]:
        """D136/D298 — todos os itens `PENDENTE`/`FALHOU` da Sessão, ordenados por
        `sequencia_local` — nunca por ordem de chegada/criação da linha."""
        ...
