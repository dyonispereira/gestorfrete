from __future__ import annotations

from enum import StrEnum


class MetricTemporalGranularity(StrEnum):
    DIARIO = "DIARIO"
    SEMANAL = "SEMANAL"
    MENSAL = "MENSAL"
    POR_EVENTO = "POR_EVENTO"
