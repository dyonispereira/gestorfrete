from __future__ import annotations

from enum import StrEnum


class CiotStatus(StrEnum):
    PENDENTE = "PENDENTE"
    REGISTRADO = "REGISTRADO"
    CANCELADO = "CANCELADO"
