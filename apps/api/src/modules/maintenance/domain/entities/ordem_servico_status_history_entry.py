from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class OrdemServicoStatusHistoryEntry(BaseEntity[uuid.UUID]):
    """`ordens_servico_status_history` — append-only (D017/D018)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        ordem_servico_id: uuid.UUID,
        status: str,
        usuario_id: uuid.UUID | None,
        origem: str,
        observacao: str | None,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.ordem_servico_id = ordem_servico_id
        self.status = status
        self.usuario_id = usuario_id
        self.origem = origem
        self.observacao = observacao
        self.data_hora = data_hora

    @classmethod
    def create(
        cls, *, ordem_servico_id: uuid.UUID, status: str, usuario_id: uuid.UUID | None, origem: str, now: datetime,
        observacao: str | None = None,
    ) -> "OrdemServicoStatusHistoryEntry":
        return cls(
            id=uuid.uuid4(), ordem_servico_id=ordem_servico_id, status=status, usuario_id=usuario_id,
            origem=origem, observacao=observacao, data_hora=now,
        )
