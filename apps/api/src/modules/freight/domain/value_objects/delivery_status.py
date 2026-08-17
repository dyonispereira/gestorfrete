from __future__ import annotations

from enum import StrEnum


class DeliveryStatus(StrEnum):
    PENDENTE = "PENDENTE"
    CONCLUIDA = "CONCLUIDA"
    RECUSADA = "RECUSADA"
    DEVOLVIDA = "DEVOLVIDA"
    CANCELADA = "CANCELADA"


TERMINAL_DELIVERY_STATUSES = frozenset(
    {DeliveryStatus.CONCLUIDA, DeliveryStatus.RECUSADA, DeliveryStatus.DEVOLVIDA, DeliveryStatus.CANCELADA}
)
