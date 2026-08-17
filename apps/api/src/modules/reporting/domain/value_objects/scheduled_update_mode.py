from __future__ import annotations

from enum import StrEnum


class ScheduledUpdateMode(StrEnum):
    TEMPO_REAL = "TEMPO_REAL"
    INCREMENTAL = "INCREMENTAL"
    DIARIO = "DIARIO"
    MANUAL = "MANUAL"
