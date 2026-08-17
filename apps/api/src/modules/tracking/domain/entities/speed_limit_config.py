from __future__ import annotations

import uuid

from core.exceptions.base import ValidationError
from modules.tracking.domain.value_objects.speed_limit_config_status import SpeedLimitConfigStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class SpeedLimitConfig(BaseAggregateRoot[uuid.UUID]):
    """`configuracoes_limite_velocidade` — `categoria_veiculo_id` ausente = padrão do tenant."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        categoria_veiculo_id: uuid.UUID | None,
        limite_kmh: float,
        status: SpeedLimitConfigStatus,
    ) -> None:
        super().__init__(id)
        self.categoria_veiculo_id = categoria_veiculo_id
        self.limite_kmh = limite_kmh
        self.status = status

    @classmethod
    def create(cls, *, categoria_veiculo_id: uuid.UUID | None, limite_kmh: float) -> "SpeedLimitConfig":
        if limite_kmh <= 0:
            raise ValidationError("TRACKING_SPEED_LIMIT_CONFIG_INVALID_LIMIT", "limite_kmh deve ser maior que zero.")
        return cls(
            id=uuid.uuid4(), categoria_veiculo_id=categoria_veiculo_id, limite_kmh=limite_kmh,
            status=SpeedLimitConfigStatus.ATIVA,
        )

    def update(self, *, limite_kmh: float | None, status: SpeedLimitConfigStatus | None) -> None:
        if limite_kmh is not None:
            if limite_kmh <= 0:
                raise ValidationError(
                    "TRACKING_SPEED_LIMIT_CONFIG_INVALID_LIMIT", "limite_kmh deve ser maior que zero."
                )
            self.limite_kmh = limite_kmh
        if status is not None:
            self.status = status
