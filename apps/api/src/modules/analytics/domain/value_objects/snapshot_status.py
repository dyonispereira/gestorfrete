from __future__ import annotations

from enum import StrEnum


class SnapshotStatus(StrEnum):
    EM_PROCESSAMENTO = "EM_PROCESSAMENTO"
    CONSOLIDADO = "CONSOLIDADO"
    INVALIDO = "INVALIDO"
