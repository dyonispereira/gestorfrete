from __future__ import annotations

from enum import StrEnum


class FaixaDistanciaMode(StrEnum):
    """Resolve a ambiguidade entre tarifa por km dentro de uma faixa e preço fixo pela faixa
    inteira — obrigatório quando `PriceTableUnit.FAIXA_DISTANCIA`."""

    TARIFA_POR_KM = "TARIFA_POR_KM"
    VALOR_FIXO = "VALOR_FIXO"
