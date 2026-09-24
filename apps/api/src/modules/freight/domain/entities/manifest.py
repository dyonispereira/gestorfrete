from __future__ import annotations

import uuid

from core.exceptions.base import DomainError
from modules.freight.domain.entities.cargo_item import CargoItem, CargoItemSpec
from shared_kernel.domain.base_entity import BaseEntity


class Manifest(BaseEntity[uuid.UUID]):
    """`romaneios` — sub-recurso de `Trip` (filho do agregado Viagem), agrupa Item de Carga
    (`002-operacao.md`). Invariante: deve ter ao menos um Item de Carga — reforçado aqui na
    criação, nunca deixado para o banco validar sozinho."""

    def __init__(
        self, id: uuid.UUID, *, viagem_id: uuid.UUID, numero_documento: str | None, itens: list[CargoItem]
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.numero_documento = numero_documento
        self.itens = itens

    @classmethod
    def create(
        cls, *, viagem_id: uuid.UUID, numero_documento: str | None, itens: list[CargoItemSpec]
    ) -> "Manifest":
        if not itens:
            raise DomainError(
                "FREIGHT_MANIFEST_REQUIRES_CARGO_ITEM", "Romaneio precisa de ao menos um Item de Carga."
            )
        manifest_id = uuid.uuid4()
        cargo_items = [
            CargoItem.create(romaneio_id=manifest_id, descricao=spec.descricao, peso=spec.peso, quantidade=spec.quantidade)
            for spec in itens
        ]
        return cls(id=manifest_id, viagem_id=viagem_id, numero_documento=numero_documento, itens=cargo_items)
