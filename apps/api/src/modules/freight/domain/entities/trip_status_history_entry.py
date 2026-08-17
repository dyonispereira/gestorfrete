from __future__ import annotations

import uuid
from datetime import datetime

from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from shared_kernel.domain.base_entity import BaseEntity


class TripStatusHistoryEntry(BaseEntity[uuid.UUID]):
    """`viagem_status_history` — append-only (D017/D018), nunca editada/removida depois de criada.
    Fonte de verdade da Timeline (`019-trip-timeline.md`) e da restauração de estado em
    `commands/retomar` (D377)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        dimensao: StatusHistoryDimension,
        status: str,
        usuario_id: uuid.UUID | None,
        origem: str,
        data_hora: datetime,
        observacao: str | None,
        latitude: float | None,
        longitude: float | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.dimensao = dimensao
        self.status = status
        self.usuario_id = usuario_id
        self.origem = origem
        self.data_hora = data_hora
        self.observacao = observacao
        self.latitude = latitude
        self.longitude = longitude

    @classmethod
    def create(
        cls,
        *,
        viagem_id: uuid.UUID,
        dimensao: StatusHistoryDimension,
        status: str,
        usuario_id: uuid.UUID | None,
        origem: str,
        now: datetime,
        observacao: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> "TripStatusHistoryEntry":
        return cls(
            id=uuid.uuid4(),
            viagem_id=viagem_id,
            dimensao=dimensao,
            status=status,
            usuario_id=usuario_id,
            origem=origem,
            data_hora=now,
            observacao=observacao,
            latitude=latitude,
            longitude=longitude,
        )
