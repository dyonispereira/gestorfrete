from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class Collection(BaseEntity[uuid.UUID]):
    """`coletas` — sub-recurso de `Trip` (D188-style, filho do agregado Viagem), marco pontual sem
    ciclo de vida próprio (`002-operacao.md`). `local` (Geography) existe na tabela física mas não
    é populado por este comando ainda — mesmo gap já documentado para `Occurrence.latitude/
    longitude` (`017-trip-occurrences.md`); captura de geolocalização fica para quando o app do
    Motorista integrar este fluxo (`freight.pickup.create` já tem `App: ●` no RBAC_MATRIX)."""

    def __init__(self, id: uuid.UUID, *, viagem_id: uuid.UUID, data_hora: datetime, conferencia_ok: bool) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.data_hora = data_hora
        self.conferencia_ok = conferencia_ok

    @classmethod
    def create(cls, *, viagem_id: uuid.UUID, conferencia_ok: bool, now: datetime) -> "Collection":
        return cls(id=uuid.uuid4(), viagem_id=viagem_id, data_hora=now, conferencia_ok=conferencia_ok)
