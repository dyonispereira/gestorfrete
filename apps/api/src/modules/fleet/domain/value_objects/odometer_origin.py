from __future__ import annotations

from enum import StrEnum


class OdometerOrigin(StrEnum):
    ABASTECIMENTO = "ABASTECIMENTO"
    CHECKLIST = "CHECKLIST"
    MANUAL = "MANUAL"
    TELEMETRIA = "TELEMETRIA"
