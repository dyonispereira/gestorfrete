from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.maintenance.domain.entities.item_ordem_servico import ItemOrdemServico


@dataclass(frozen=True)
class ItemOrdemServicoDTO:
    id: uuid.UUID
    ordem_servico_id: uuid.UUID
    categoria_custo: str
    descricao: str
    peca_estoque_id: uuid.UUID | None
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal

    @staticmethod
    def from_entity(entity: ItemOrdemServico) -> "ItemOrdemServicoDTO":
        return ItemOrdemServicoDTO(
            id=entity.id, ordem_servico_id=entity.ordem_servico_id, categoria_custo=entity.categoria_custo.value,
            descricao=entity.descricao, peca_estoque_id=entity.peca_estoque_id, quantidade=entity.quantidade,
            valor_unitario=entity.valor_unitario, valor_total=entity.valor_total,
        )
