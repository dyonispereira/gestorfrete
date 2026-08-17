from __future__ import annotations

import uuid

from modules.tracking.domain.value_objects.tracking_provider_status import TrackingProviderStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class TrackingProvider(BaseAggregateRoot[uuid.UUID]):
    """`provedores_rastreamento` — cadastro puro (D291), sem integração específica por fornecedor
    modelada aqui."""

    def __init__(self, id: uuid.UUID, *, nome: str, status: TrackingProviderStatus) -> None:
        super().__init__(id)
        self.nome = nome
        self.status = status

    @classmethod
    def create(cls, *, nome: str) -> "TrackingProvider":
        return cls(id=uuid.uuid4(), nome=nome, status=TrackingProviderStatus.ATIVO)

    def update(self, *, nome: str | None, status: TrackingProviderStatus | None) -> None:
        if nome is not None:
            self.nome = nome
        if status is not None:
            self.status = status
