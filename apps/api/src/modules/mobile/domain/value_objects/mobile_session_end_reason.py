from __future__ import annotations

from enum import StrEnum


class MobileSessionEndReason(StrEnum):
    LOGOUT = "LOGOUT"
    REVOGACAO_ADMINISTRATIVA = "REVOGACAO_ADMINISTRATIVA"
    TROCA_DE_DISPOSITIVO = "TROCA_DE_DISPOSITIVO"
