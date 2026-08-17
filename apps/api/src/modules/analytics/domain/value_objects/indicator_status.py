from __future__ import annotations

from enum import StrEnum


class IndicatorStatus(StrEnum):
    VALIDO = "VALIDO"
    RECALCULADO = "RECALCULADO"
    SNAPSHOTADO = "SNAPSHOTADO"
