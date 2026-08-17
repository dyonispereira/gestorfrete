from __future__ import annotations

from enum import StrEnum


class PayableOrigin(StrEnum):
    VIAGEM = "VIAGEM"
    ORDEM_SERVICO = "ORDEM_SERVICO"
    ABASTECIMENTO = "ABASTECIMENTO"
    COMPRA = "COMPRA"
    AJUSTE_MANUAL = "AJUSTE_MANUAL"
