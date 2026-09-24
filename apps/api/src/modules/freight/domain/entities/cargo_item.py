from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from core.exceptions.base import DomainError
from shared_kernel.domain.base_entity import BaseEntity


@dataclass(frozen=True)
class CargoItemSpec:
    """Entrada para `Manifest.create(...)` — antes de existir um `romaneio_id` real (o Romaneio
    ainda não foi criado nesse ponto), nunca uma `CargoItem` incompleta."""

    descricao: str
    peso: Decimal
    quantidade: int


class CargoItem(BaseEntity[uuid.UUID]):
    """`itens_carga` — nunca existe fora de um Romaneio (D005/D006, `002-operacao.md`)."""

    def __init__(
        self, id: uuid.UUID, *, romaneio_id: uuid.UUID, descricao: str, peso: Decimal, quantidade: int
    ) -> None:
        super().__init__(id)
        self.romaneio_id = romaneio_id
        self.descricao = descricao
        self.peso = peso
        self.quantidade = quantidade

    @classmethod
    def create(cls, *, romaneio_id: uuid.UUID, descricao: str, peso: Decimal, quantidade: int) -> "CargoItem":
        if peso <= 0:
            raise DomainError("FREIGHT_CARGO_ITEM_PESO_INVALIDO", "Peso do Item de Carga precisa ser maior que zero.")
        if quantidade <= 0:
            raise DomainError(
                "FREIGHT_CARGO_ITEM_QUANTIDADE_INVALIDA", "Quantidade do Item de Carga precisa ser maior que zero."
            )
        return cls(id=uuid.uuid4(), romaneio_id=romaneio_id, descricao=descricao, peso=peso, quantidade=quantidade)
