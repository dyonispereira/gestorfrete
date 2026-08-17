from __future__ import annotations

from enum import StrEnum


class MdfeStatus(StrEnum):
    PENDENTE = "PENDENTE"
    AUTORIZADO = "AUTORIZADO"
    ENCERRADO = "ENCERRADO"
    CANCELADO = "CANCELADO"
