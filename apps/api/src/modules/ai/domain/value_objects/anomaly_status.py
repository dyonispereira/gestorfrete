from __future__ import annotations

from enum import StrEnum


class AnomalyStatus(StrEnum):
    ABERTA = "ABERTA"
    INVESTIGADA = "INVESTIGADA"
    DESCARTADA = "DESCARTADA"
