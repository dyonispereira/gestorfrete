from __future__ import annotations

from enum import StrEnum


class FiscalEventResult(StrEnum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    TIMEOUT = "TIMEOUT"
