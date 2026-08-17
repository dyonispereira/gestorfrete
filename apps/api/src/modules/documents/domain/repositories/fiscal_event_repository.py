from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.documents.domain.entities.fiscal_event import FiscalEvent
from shared_kernel.domain.repository import Repository


class FiscalEventRepository(Repository[FiscalEvent, uuid.UUID]):
    @abstractmethod
    async def exists_with_protocol(
        self, *, documento_tipo: str, documento_id: uuid.UUID, protocolo_externo: str
    ) -> bool: ...

    @abstractmethod
    async def list_page(
        self,
        *,
        cursor_data_hora: datetime | None,
        cursor_id: uuid.UUID | None,
        limit: int,
        documento_tipo: str | None,
        documento_id: uuid.UUID | None,
        protocolo_externo: str | None,
        started_at_from: datetime | None,
        started_at_to: datetime | None,
        resultado: str | None,
        origem: str | None,
        numero_tentativa: int | None,
    ) -> list[FiscalEvent]: ...
