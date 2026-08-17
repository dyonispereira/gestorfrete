from __future__ import annotations

from enum import StrEnum


class FitnessStatus(StrEnum):
    """`status_aptidao` — recalculado por `block()`/`unblock()`, nunca escrito diretamente pelo
    cliente da API (`readOnly` no contrato, `009-drivers.md`)."""

    APTO = "APTO"
    BLOQUEADO = "BLOQUEADO"
