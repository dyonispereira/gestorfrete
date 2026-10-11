from __future__ import annotations

from enum import StrEnum


class PriceTableUnit(StrEnum):
    """Unidade de cálculo de um `ItemTabelaPreco` — decide a fórmula usada por
    `PriceCalculationService` (`application/price_calculation_service.py`). `PERCENTUAL` exige
    `base_percentual_descricao` no item e `base_percentual_valor` explícito no comando de aplicação
    — nunca uma base inventada ou herdada de `receita_prevista_snapshot`."""

    VIAGEM = "VIAGEM"
    KM = "KM"
    TONELADA = "TONELADA"
    KG = "KG"
    FAIXA_DISTANCIA = "FAIXA_DISTANCIA"
    PERCENTUAL = "PERCENTUAL"
