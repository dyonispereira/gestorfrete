from __future__ import annotations

import uuid

from shared_kernel.domain.base_entity import BaseEntity


class LocationOrigin(BaseEntity[uuid.UUID]):
    """`origens_localizacao` — Platform Reference Data (D046), sem `tenant_id`. Catálogo aberto
    (`TEXT UNIQUE`, nunca Enum fechado) para admitir fontes novas sem alteração de sistema. Não é
    Aggregate Root de escrita — só `GET /tracking/origins` existe (`048-vehicle-positions.md`)."""

    def __init__(self, id: uuid.UUID, *, nome: str, precisao_tipica_metros: float | None) -> None:
        super().__init__(id)
        self.nome = nome
        self.precisao_tipica_metros = precisao_tipica_metros
