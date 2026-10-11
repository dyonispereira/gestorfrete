from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ConflictError
from shared_kernel.domain.base_entity import BaseEntity


class TripPriceApplication(BaseEntity[uuid.UUID]):
    """`aplicacoes_tabela_preco_viagem` — filha de `Trip` (não é Aggregate Root, mesmo padrão de
    `InvoiceTrip`/`CargoItem`). Append-only (D109-consistent): `remove()` nunca apaga a linha, só
    marca `removido_em`/`removido_por` — a evidência de negociação permanece mesmo depois de
    desfeita. `direcao`/`unidade_calculo` são snapshots em texto puro (não os enums de `pricing`) —
    `freight` nunca importa o domínio de outro bounded context (D033/D034), só referencia por ID."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        tabela_preco_id: uuid.UUID,
        item_tabela_preco_id: uuid.UUID,
        tabela_preco_versao: int,
        direcao: str,
        unidade_calculo: str,
        quantidade_utilizada: Decimal | None,
        base_percentual_valor: Decimal | None,
        tarifa_aplicada: Decimal,
        valor_minimo_aplicado: Decimal | None,
        adicional_fixo_aplicado: Decimal | None,
        desconto_fixo_aplicado: Decimal | None,
        adicional_percentual_aplicado: Decimal | None,
        desconto_percentual_aplicado: Decimal | None,
        valor_calculado_bruto: Decimal,
        valor_final: Decimal,
        aplicado_em: datetime,
        aplicado_por: uuid.UUID,
        removido_em: datetime | None,
        removido_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.tabela_preco_id = tabela_preco_id
        self.item_tabela_preco_id = item_tabela_preco_id
        self.tabela_preco_versao = tabela_preco_versao
        self.direcao = direcao
        self.unidade_calculo = unidade_calculo
        self.quantidade_utilizada = quantidade_utilizada
        self.base_percentual_valor = base_percentual_valor
        self.tarifa_aplicada = tarifa_aplicada
        self.valor_minimo_aplicado = valor_minimo_aplicado
        self.adicional_fixo_aplicado = adicional_fixo_aplicado
        self.desconto_fixo_aplicado = desconto_fixo_aplicado
        self.adicional_percentual_aplicado = adicional_percentual_aplicado
        self.desconto_percentual_aplicado = desconto_percentual_aplicado
        self.valor_calculado_bruto = valor_calculado_bruto
        self.valor_final = valor_final
        self.aplicado_em = aplicado_em
        self.aplicado_por = aplicado_por
        self.removido_em = removido_em
        self.removido_por = removido_por

    @property
    def is_active(self) -> bool:
        return self.removido_em is None

    @classmethod
    def create(
        cls,
        *,
        viagem_id: uuid.UUID,
        tabela_preco_id: uuid.UUID,
        item_tabela_preco_id: uuid.UUID,
        tabela_preco_versao: int,
        direcao: str,
        unidade_calculo: str,
        quantidade_utilizada: Decimal | None,
        base_percentual_valor: Decimal | None,
        tarifa_aplicada: Decimal,
        valor_minimo_aplicado: Decimal | None,
        adicional_fixo_aplicado: Decimal | None,
        desconto_fixo_aplicado: Decimal | None,
        adicional_percentual_aplicado: Decimal | None,
        desconto_percentual_aplicado: Decimal | None,
        valor_calculado_bruto: Decimal,
        valor_final: Decimal,
        aplicado_por: uuid.UUID,
        now: datetime,
    ) -> "TripPriceApplication":
        return cls(
            id=uuid.uuid4(),
            viagem_id=viagem_id,
            tabela_preco_id=tabela_preco_id,
            item_tabela_preco_id=item_tabela_preco_id,
            tabela_preco_versao=tabela_preco_versao,
            direcao=direcao,
            unidade_calculo=unidade_calculo,
            quantidade_utilizada=quantidade_utilizada,
            base_percentual_valor=base_percentual_valor,
            tarifa_aplicada=tarifa_aplicada,
            valor_minimo_aplicado=valor_minimo_aplicado,
            adicional_fixo_aplicado=adicional_fixo_aplicado,
            desconto_fixo_aplicado=desconto_fixo_aplicado,
            adicional_percentual_aplicado=adicional_percentual_aplicado,
            desconto_percentual_aplicado=desconto_percentual_aplicado,
            valor_calculado_bruto=valor_calculado_bruto,
            valor_final=valor_final,
            aplicado_em=now,
            aplicado_por=aplicado_por,
            removido_em=None,
            removido_por=None,
        )

    def remove(self, *, removed_by: uuid.UUID, now: datetime) -> None:
        if not self.is_active:
            raise ConflictError(
                "FREIGHT_PRICE_APPLICATION_ALREADY_REMOVED", "Esta aplicação de tabela de frete já foi removida."
            )
        self.removido_em = now
        self.removido_por = removed_by
