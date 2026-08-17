from __future__ import annotations

from enum import StrEnum


class CteStatus(StrEnum):
    RASCUNHO = "RASCUNHO"
    VALIDADO = "VALIDADO"
    ASSINADO = "ASSINADO"
    TRANSMITIDO = "TRANSMITIDO"
    AUTORIZADO = "AUTORIZADO"
    CANCELADO = "CANCELADO"
    DENEGADO = "DENEGADO"
    INUTILIZADO = "INUTILIZADO"
