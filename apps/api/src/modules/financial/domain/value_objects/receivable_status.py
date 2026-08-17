from __future__ import annotations

from enum import StrEnum


class ReceivableStatus(StrEnum):
    PENDENTE = "PENDENTE"
    VENCIDA = "VENCIDA"
    RECEBIDA = "RECEBIDA"
    CONCILIADA = "CONCILIADA"
