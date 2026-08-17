from __future__ import annotations

from enum import StrEnum


class ModelStatus(StrEnum):
    EM_TREINAMENTO = "EM_TREINAMENTO"
    ATIVO = "ATIVO"
    DESCONTINUADO = "DESCONTINUADO"
