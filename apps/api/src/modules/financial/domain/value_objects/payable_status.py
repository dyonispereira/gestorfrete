from __future__ import annotations

from enum import StrEnum


class PayableStatus(StrEnum):
    LANCADA = "LANCADA"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    APROVADA = "APROVADA"
    PAGA = "PAGA"
    CONCILIADA = "CONCILIADA"
    REJEITADA = "REJEITADA"
