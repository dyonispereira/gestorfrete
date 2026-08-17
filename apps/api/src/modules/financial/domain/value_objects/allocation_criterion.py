from __future__ import annotations

from enum import StrEnum


class AllocationCriterion(StrEnum):
    KM_RODADO = "KM_RODADO"
    NUMERO_VIAGENS = "NUMERO_VIAGENS"
    PESO_TRANSPORTADO = "PESO_TRANSPORTADO"
