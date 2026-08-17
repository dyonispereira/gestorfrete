from __future__ import annotations

import uuid
from datetime import datetime

from modules.financial.domain.value_objects.payable_status import PayableStatus
from shared_kernel.domain.base_entity import BaseEntity


class PayableStatusHistoryEntry(BaseEntity[uuid.UUID]):
    """`contas_pagar_status_history` — append-only (D017/D018). Auditoria #2 do usuário: toda
    transição, incluindo as derivadas, grava uma linha aqui."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        conta_pagar_id: uuid.UUID,
        status: PayableStatus,
        usuario_id: uuid.UUID | None,
        observacao: str | None,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.conta_pagar_id = conta_pagar_id
        self.status = status
        self.usuario_id = usuario_id
        self.observacao = observacao
        self.data_hora = data_hora

    @classmethod
    def create(
        cls,
        *,
        conta_pagar_id: uuid.UUID,
        status: PayableStatus,
        usuario_id: uuid.UUID | None,
        now: datetime,
        observacao: str | None = None,
    ) -> "PayableStatusHistoryEntry":
        return cls(
            id=uuid.uuid4(), conta_pagar_id=conta_pagar_id, status=status, usuario_id=usuario_id,
            observacao=observacao, data_hora=now,
        )
