from __future__ import annotations

import uuid
from datetime import datetime

from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from shared_kernel.domain.base_entity import BaseEntity


class ReceivableStatusHistoryEntry(BaseEntity[uuid.UUID]):
    """`contas_receber_status_history` — append-only (D017/D018)."""

    def __init__(
        self, id: uuid.UUID, *, conta_receber_id: uuid.UUID, status: ReceivableStatus, usuario_id: uuid.UUID | None,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.conta_receber_id = conta_receber_id
        self.status = status
        self.usuario_id = usuario_id
        self.data_hora = data_hora

    @classmethod
    def create(
        cls, *, conta_receber_id: uuid.UUID, status: ReceivableStatus, usuario_id: uuid.UUID | None, now: datetime
    ) -> "ReceivableStatusHistoryEntry":
        return cls(
            id=uuid.uuid4(), conta_receber_id=conta_receber_id, status=status, usuario_id=usuario_id, data_hora=now
        )
