from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Heartbeat(BaseAggregateRoot[uuid.UUID]):
    """`heartbeats` — Time Series técnico (D105), não de negócio. Única exceção ao esqueleto D191:
    `capturado_em` pode ser `None` (heartbeat nem sempre informa captura); particiona por
    `recebido_em`, sempre presente."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        equipamento_rastreamento_id: uuid.UUID,
        protocolo_externo: str | None,
        capturado_em: datetime | None,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.equipamento_rastreamento_id = equipamento_rastreamento_id
        self.protocolo_externo = protocolo_externo
        self.capturado_em = capturado_em
        self.recebido_em = recebido_em
        self.processado_em = processado_em

    @classmethod
    def create(
        cls,
        *,
        equipamento_rastreamento_id: uuid.UUID,
        protocolo_externo: str | None = None,
        capturado_em: datetime | None = None,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> "Heartbeat":
        return cls(
            id=uuid.uuid4(), equipamento_rastreamento_id=equipamento_rastreamento_id,
            protocolo_externo=protocolo_externo, capturado_em=capturado_em, recebido_em=recebido_em,
            processado_em=processado_em,
        )
