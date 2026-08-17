from __future__ import annotations

from enum import StrEnum


class TripFinancialStatus(StrEnum):
    AGUARDANDO_FATURAMENTO = "AGUARDANDO_FATURAMENTO"
    FATURADA = "FATURADA"
    AGUARDANDO_RECEBIMENTO = "AGUARDANDO_RECEBIMENTO"
    RECEBIDA = "RECEBIDA"
