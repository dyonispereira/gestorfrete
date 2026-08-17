from __future__ import annotations

import uuid
from decimal import Decimal

from modules.financial.domain.value_objects.allocation_criterion import AllocationCriterion
from shared_kernel.domain.base_entity import BaseEntity


class ExpenseAllocation(BaseEntity[uuid.UUID]):
    """`rateios_despesa` — Rateio de Despesa. D393: criado automaticamente ao lançar uma Conta a
    Pagar com `origin ∈ {VIAGEM, ORDEM_SERVICO}`, aloca 100% do valor a um único alvo (algoritmo
    proporcional real fora de escopo). Alimenta `viagens.custo_realizado` via
    `TripInternalTransitions` (D390)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        conta_pagar_id: uuid.UUID,
        centro_custo_id: uuid.UUID | None,
        viagem_id: uuid.UUID | None,
        criterio: AllocationCriterion,
        valor_rateado: Decimal,
    ) -> None:
        super().__init__(id)
        self.conta_pagar_id = conta_pagar_id
        self.centro_custo_id = centro_custo_id
        self.viagem_id = viagem_id
        self.criterio = criterio
        self.valor_rateado = valor_rateado

    @classmethod
    def create(
        cls,
        *,
        conta_pagar_id: uuid.UUID,
        centro_custo_id: uuid.UUID | None,
        viagem_id: uuid.UUID | None,
        valor_rateado: Decimal,
    ) -> "ExpenseAllocation":
        return cls(
            id=uuid.uuid4(), conta_pagar_id=conta_pagar_id, centro_custo_id=centro_custo_id, viagem_id=viagem_id,
            criterio=AllocationCriterion.NUMERO_VIAGENS, valor_rateado=valor_rateado,
        )
