from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from core.exceptions.base import ValidationError
from modules.pricing.domain.entities.price_table_item import PriceTableItem
from modules.pricing.domain.value_objects.faixa_distancia_mode import FaixaDistanciaMode
from modules.pricing.domain.value_objects.price_table_unit import PriceTableUnit

_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class PriceCalculationResult:
    quantidade_utilizada: Decimal | None
    valor_calculado_bruto: Decimal
    valor_final: Decimal


def calculate(
    item: PriceTableItem,
    *,
    distancia_prevista_km: Decimal | None,
    toneladas_carga: Decimal | None,
    peso_carga_kg: Decimal | None,
    base_percentual_valor: Decimal | None,
) -> PriceCalculationResult:
    """Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — único lugar do sistema que calcula o valor de uma
    aplicação de Tabela de Frete. Ordem determinística, documentada e nunca alterada por conveniência:
    1. valor_base (conforme `unidade_calculo`)
    2. + adicional_fixo
    3. - desconto_fixo
    4. × (1 + adicional_percentual / 100)
    5. × (1 - desconto_percentual / 100)
    6. valor_minimo aplicado por último (`max(resultado, valor_minimo)`)
    7. arredondamento `ROUND_HALF_UP` em 2 casas só no passo final — nunca em etapas intermediárias
       (evita erro de arredondamento composto).
    `PERCENTUAL` nunca infere a base sozinho — `base_percentual_valor` é sempre exigido
    explicitamente pelo chamador, nunca o `receita_prevista_snapshot`/qualquer outro valor
    "adivinhado" da Viagem."""

    quantidade_utilizada: Decimal | None
    valor_base: Decimal

    if item.unidade_calculo == PriceTableUnit.VIAGEM:
        quantidade_utilizada = None
        valor_base = item.valor

    elif item.unidade_calculo == PriceTableUnit.KM:
        if distancia_prevista_km is None:
            raise ValidationError(
                "PRICING_CALCULATION_DISTANCIA_AUSENTE",
                "Viagem precisa ter distancia_prevista_km informada para aplicar item por KM.",
            )
        quantidade_utilizada = distancia_prevista_km
        valor_base = item.valor * distancia_prevista_km

    elif item.unidade_calculo == PriceTableUnit.TONELADA:
        if toneladas_carga is None:
            raise ValidationError(
                "PRICING_CALCULATION_PESO_AUSENTE",
                "Viagem precisa ter peso_carga_kg informado para aplicar item por TONELADA.",
            )
        quantidade_utilizada = toneladas_carga
        valor_base = item.valor * toneladas_carga

    elif item.unidade_calculo == PriceTableUnit.KG:
        if peso_carga_kg is None:
            raise ValidationError(
                "PRICING_CALCULATION_PESO_AUSENTE",
                "Viagem precisa ter peso_carga_kg informado para aplicar item por KG.",
            )
        quantidade_utilizada = peso_carga_kg
        valor_base = item.valor * peso_carga_kg

    elif item.unidade_calculo == PriceTableUnit.FAIXA_DISTANCIA:
        if distancia_prevista_km is None:
            raise ValidationError(
                "PRICING_CALCULATION_DISTANCIA_AUSENTE",
                "Viagem precisa ter distancia_prevista_km informada para aplicar item por FAIXA_DISTANCIA.",
            )
        assert item.faixa_distancia_min_km is not None and item.faixa_distancia_max_km is not None
        if not (item.faixa_distancia_min_km <= distancia_prevista_km <= item.faixa_distancia_max_km):
            raise ValidationError(
                "PRICING_CALCULATION_FORA_DA_FAIXA",
                f"distancia_prevista_km ({distancia_prevista_km}) fora da faixa do item "
                f"[{item.faixa_distancia_min_km}, {item.faixa_distancia_max_km}].",
            )
        quantidade_utilizada = distancia_prevista_km
        if item.faixa_modo == FaixaDistanciaMode.TARIFA_POR_KM:
            valor_base = item.valor * distancia_prevista_km
        else:
            valor_base = item.valor

    elif item.unidade_calculo == PriceTableUnit.PERCENTUAL:
        if base_percentual_valor is None:
            raise ValidationError(
                "PRICING_CALCULATION_BASE_PERCENTUAL_AUSENTE",
                "Item PERCENTUAL exige base_percentual_valor explícita no comando de aplicação — "
                "nunca uma base inventada ou herdada da Viagem.",
            )
        quantidade_utilizada = None
        valor_base = (item.valor / Decimal("100")) * base_percentual_valor

    else:  # pragma: no cover - exaustivo por construção do enum
        raise ValidationError("PRICING_CALCULATION_UNIDADE_DESCONHECIDA", "Unidade de cálculo desconhecida.")

    valor = valor_base
    if item.adicional_fixo is not None:
        valor += item.adicional_fixo
    if item.desconto_fixo is not None:
        valor -= item.desconto_fixo
    if item.adicional_percentual is not None:
        valor *= Decimal("1") + (item.adicional_percentual / Decimal("100"))
    if item.desconto_percentual is not None:
        valor *= Decimal("1") - (item.desconto_percentual / Decimal("100"))

    valor_calculado_bruto = valor
    valor_final = valor_calculado_bruto
    if item.valor_minimo is not None and valor_final < item.valor_minimo:
        valor_final = item.valor_minimo

    valor_calculado_bruto = valor_calculado_bruto.quantize(_CENTS, rounding=ROUND_HALF_UP)
    valor_final = valor_final.quantize(_CENTS, rounding=ROUND_HALF_UP)

    if valor_final < 0:
        raise ValidationError(
            "PRICING_CALCULATION_VALOR_NEGATIVO",
            "O cálculo resultou em valor final negativo — confira descontos/percentuais do item.",
        )

    return PriceCalculationResult(
        quantidade_utilizada=quantidade_utilizada, valor_calculado_bruto=valor_calculado_bruto,
        valor_final=valor_final,
    )
