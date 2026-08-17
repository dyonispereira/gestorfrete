from __future__ import annotations

from enum import StrEnum


class InferenceStatus(StrEnum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    TIMEOUT = "TIMEOUT"
