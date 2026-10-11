from __future__ import annotations

from enum import StrEnum


class PriceTableStatus(StrEnum):
    RASCUNHO = "RASCUNHO"
    VIGENTE = "VIGENTE"
    EXPIRADA = "EXPIRADA"
