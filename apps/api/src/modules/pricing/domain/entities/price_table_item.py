from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ValidationError
from modules.pricing.domain.value_objects.faixa_distancia_mode import FaixaDistanciaMode
from modules.pricing.domain.value_objects.price_table_unit import PriceTableUnit
from shared_kernel.domain.base_entity import BaseEntity


class PriceTableItem(BaseEntity[uuid.UUID]):
    """`itens_tabela_preco` — filho de `PriceTable` (não é Aggregate Root, mesmo padrão de
    `InvoiceTrip`/`CargoItem`). Imutável assim que a `PriceTable` dona sai de `RASCUNHO`
    (`PriceTableRepository` só permite `add()`/`delete()` de item enquanto a tabela está
    `RASCUNHO` — a regra vive no Handler, que consulta o status da tabela antes de mutar)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tabela_preco_id: uuid.UUID,
        unidade_calculo: PriceTableUnit,
        categoria_veiculo_id: uuid.UUID | None,
        origem_uf: str | None,
        destino_uf: str | None,
        faixa_distancia_min_km: Decimal | None,
        faixa_distancia_max_km: Decimal | None,
        faixa_modo: FaixaDistanciaMode | None,
        valor: Decimal,
        valor_minimo: Decimal | None,
        adicional_fixo: Decimal | None,
        desconto_fixo: Decimal | None,
        adicional_percentual: Decimal | None,
        desconto_percentual: Decimal | None,
        base_percentual_descricao: str | None,
        criado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.criado_em = criado_em
        self.tabela_preco_id = tabela_preco_id
        self.unidade_calculo = unidade_calculo
        self.categoria_veiculo_id = categoria_veiculo_id
        self.origem_uf = origem_uf
        self.destino_uf = destino_uf
        self.faixa_distancia_min_km = faixa_distancia_min_km
        self.faixa_distancia_max_km = faixa_distancia_max_km
        self.faixa_modo = faixa_modo
        self.valor = valor
        self.valor_minimo = valor_minimo
        self.adicional_fixo = adicional_fixo
        self.desconto_fixo = desconto_fixo
        self.adicional_percentual = adicional_percentual
        self.desconto_percentual = desconto_percentual
        self.base_percentual_descricao = base_percentual_descricao

    @classmethod
    def create(
        cls,
        *,
        tabela_preco_id: uuid.UUID,
        unidade_calculo: PriceTableUnit,
        categoria_veiculo_id: uuid.UUID | None,
        origem_uf: str | None,
        destino_uf: str | None,
        faixa_distancia_min_km: Decimal | None,
        faixa_distancia_max_km: Decimal | None,
        faixa_modo: FaixaDistanciaMode | None,
        valor: Decimal,
        valor_minimo: Decimal | None,
        adicional_fixo: Decimal | None,
        desconto_fixo: Decimal | None,
        adicional_percentual: Decimal | None,
        desconto_percentual: Decimal | None,
        base_percentual_descricao: str | None,
        now: datetime,
    ) -> "PriceTableItem":
        if valor <= 0:
            raise ValidationError("PRICING_ITEM_VALOR_INVALIDO", "Valor do item precisa ser maior que zero.")
        if valor_minimo is not None and valor_minimo <= 0:
            raise ValidationError(
                "PRICING_ITEM_VALOR_MINIMO_INVALIDO", "Valor mínimo do item precisa ser maior que zero."
            )
        if unidade_calculo == PriceTableUnit.FAIXA_DISTANCIA:
            if faixa_distancia_min_km is None or faixa_distancia_max_km is None or faixa_modo is None:
                raise ValidationError(
                    "PRICING_ITEM_FAIXA_DISTANCIA_INCOMPLETA",
                    "FAIXA_DISTANCIA exige faixa_distancia_min_km, faixa_distancia_max_km e faixa_modo "
                    "(evita ambiguidade entre tarifa por km e valor fixo pela faixa).",
                )
            if faixa_distancia_max_km <= faixa_distancia_min_km:
                raise ValidationError(
                    "PRICING_ITEM_FAIXA_DISTANCIA_INVALIDA", "faixa_distancia_max_km deve ser maior que o mínimo."
                )
        if unidade_calculo == PriceTableUnit.PERCENTUAL and not base_percentual_descricao:
            raise ValidationError(
                "PRICING_ITEM_PERCENTUAL_SEM_BASE",
                "PERCENTUAL exige base_percentual_descricao explícita — nunca uma base inventada.",
            )
        return cls(
            id=uuid.uuid4(),
            tabela_preco_id=tabela_preco_id,
            unidade_calculo=unidade_calculo,
            categoria_veiculo_id=categoria_veiculo_id,
            origem_uf=origem_uf,
            destino_uf=destino_uf,
            faixa_distancia_min_km=faixa_distancia_min_km,
            faixa_distancia_max_km=faixa_distancia_max_km,
            faixa_modo=faixa_modo,
            valor=valor,
            valor_minimo=valor_minimo,
            adicional_fixo=adicional_fixo,
            desconto_fixo=desconto_fixo,
            adicional_percentual=adicional_percentual,
            desconto_percentual=desconto_percentual,
            base_percentual_descricao=base_percentual_descricao,
            criado_em=now,
        )
