from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from modules.pricing.domain.entities.price_table import PriceTable
from modules.pricing.domain.entities.price_table_item import PriceTableItem


@dataclass(frozen=True)
class PriceTableDTO:
    id: uuid.UUID
    nome: str
    direcao: str
    versao: int
    vigencia_inicio: date
    vigencia_fim: date | None
    cliente_id: uuid.UUID | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(table: PriceTable) -> "PriceTableDTO":
        return PriceTableDTO(
            id=table.id, nome=table.nome, direcao=table.direcao.value, versao=table.versao,
            vigencia_inicio=table.vigencia_inicio, vigencia_fim=table.vigencia_fim, cliente_id=table.cliente_id,
            status=table.status.value, created_at=table.audit.created_at, created_by=table.audit.created_by,
            updated_at=table.audit.updated_at, updated_by=table.audit.updated_by,
        )


@dataclass(frozen=True)
class PriceTableItemDTO:
    id: uuid.UUID
    tabela_preco_id: uuid.UUID
    unidade_calculo: str
    categoria_veiculo_id: uuid.UUID | None
    origem_uf: str | None
    destino_uf: str | None
    faixa_distancia_min_km: Decimal | None
    faixa_distancia_max_km: Decimal | None
    faixa_modo: str | None
    valor: Decimal
    valor_minimo: Decimal | None
    adicional_fixo: Decimal | None
    desconto_fixo: Decimal | None
    adicional_percentual: Decimal | None
    desconto_percentual: Decimal | None
    base_percentual_descricao: str | None
    created_at: datetime

    @staticmethod
    def from_entity(item: PriceTableItem) -> "PriceTableItemDTO":
        return PriceTableItemDTO(
            id=item.id, tabela_preco_id=item.tabela_preco_id, unidade_calculo=item.unidade_calculo.value,
            categoria_veiculo_id=item.categoria_veiculo_id, origem_uf=item.origem_uf, destino_uf=item.destino_uf,
            faixa_distancia_min_km=item.faixa_distancia_min_km, faixa_distancia_max_km=item.faixa_distancia_max_km,
            faixa_modo=item.faixa_modo.value if item.faixa_modo else None, valor=item.valor,
            valor_minimo=item.valor_minimo, adicional_fixo=item.adicional_fixo, desconto_fixo=item.desconto_fixo,
            adicional_percentual=item.adicional_percentual, desconto_percentual=item.desconto_percentual,
            base_percentual_descricao=item.base_percentual_descricao, created_at=item.criado_em,
        )
