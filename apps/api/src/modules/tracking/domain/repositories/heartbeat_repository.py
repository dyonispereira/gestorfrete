from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.tracking.domain.entities.heartbeat import Heartbeat


class HeartbeatRepository(ABC):
    @abstractmethod
    async def add(self, heartbeat: Heartbeat) -> None: ...

    @abstractmethod
    async def exists_with_protocol(self, equipamento_rastreamento_id: uuid.UUID, protocolo_externo: str) -> bool:
        """D111 — chave de idempotência quando o Provedor oferece um identificador de sequência."""
        ...

    @abstractmethod
    async def list_page(
        self, *, equipamento_rastreamento_id: uuid.UUID, after_recebido_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, received_at_gte: datetime | None,
        received_at_lte: datetime | None,
    ) -> list[Heartbeat]: ...
