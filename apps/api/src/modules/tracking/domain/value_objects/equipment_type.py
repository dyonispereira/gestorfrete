from __future__ import annotations

from enum import StrEnum


class EquipmentType(StrEnum):
    """D128 — no máximo um `PRINCIPAL` vigente por veículo; os demais papéis coexistem livremente."""

    PRINCIPAL = "PRINCIPAL"
    BACKUP = "BACKUP"
    CAMERA = "CAMERA"
    SENSOR_TEMPERATURA = "SENSOR_TEMPERATURA"
    TPMS = "TPMS"
    OUTRO = "OUTRO"
