from __future__ import annotations

import uuid
from decimal import Decimal

from core.exceptions.base import DomainError
from modules.maintenance.domain.value_objects.item_ordem_servico_categoria_custo import (
    ItemOrdemServicoCategoriaCusto,
)
from shared_kernel.domain.base_entity import BaseEntity


class ItemOrdemServico(BaseEntity[uuid.UUID]):
    """`itens_ordem_servico` — nunca existe fora de uma OS (D005/D006, `valor_total` é `GENERATED`
    no banco). `peca_estoque_id` nasce sem FK física — `pecas_estoque` ainda não existe (mesmo
    padrão de `contas_pagar.ordem_servico_id` antes desta Lote, D387)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        ordem_servico_id: uuid.UUID,
        categoria_custo: ItemOrdemServicoCategoriaCusto,
        descricao: str,
        peca_estoque_id: uuid.UUID | None,
        quantidade: Decimal,
        valor_unitario: Decimal,
    ) -> None:
        super().__init__(id)
        self.ordem_servico_id = ordem_servico_id
        self.categoria_custo = categoria_custo
        self.descricao = descricao
        self.peca_estoque_id = peca_estoque_id
        self.quantidade = quantidade
        self.valor_unitario = valor_unitario

    @property
    def valor_total(self) -> Decimal:
        return self.quantidade * self.valor_unitario

    @classmethod
    def create(
        cls, *, ordem_servico_id: uuid.UUID, categoria_custo: ItemOrdemServicoCategoriaCusto, descricao: str,
        peca_estoque_id: uuid.UUID | None, quantidade: Decimal, valor_unitario: Decimal,
    ) -> "ItemOrdemServico":
        if quantidade <= 0:
            raise DomainError("MAINTENANCE_WORK_ORDER_ITEM_QUANTIDADE_INVALIDA", "Quantidade precisa ser maior que zero.")
        return cls(
            id=uuid.uuid4(), ordem_servico_id=ordem_servico_id, categoria_custo=categoria_custo, descricao=descricao,
            peca_estoque_id=peca_estoque_id, quantidade=quantidade, valor_unitario=valor_unitario,
        )
