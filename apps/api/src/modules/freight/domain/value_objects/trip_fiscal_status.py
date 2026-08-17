from __future__ import annotations

from enum import StrEnum


class TripFiscalStatus(StrEnum):
    PENDENTE = "PENDENTE"
    CTE_EMITIDO = "CTE_EMITIDO"
    MDFE_EMITIDO = "MDFE_EMITIDO"
    MDFE_ENCERRADO = "MDFE_ENCERRADO"
    CTE_CANCELADO = "CTE_CANCELADO"
