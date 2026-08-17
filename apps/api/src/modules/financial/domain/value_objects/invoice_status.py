from __future__ import annotations

from enum import StrEnum


class InvoiceStatus(StrEnum):
    EMITIDA = "EMITIDA"
    CANCELADA = "CANCELADA"
