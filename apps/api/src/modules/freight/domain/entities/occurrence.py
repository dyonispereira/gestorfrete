from __future__ import annotations

import uuid
from datetime import datetime

from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_status import OccurrenceStatus
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from shared_kernel.domain.base_entity import BaseEntity


class Occurrence(BaseEntity[uuid.UUID]):
    """`ocorrencias` — sub-recurso de `Trip` (D232), genérica por design (D076): uma única
    entidade cobre todo `tipo`, nunca uma API por tipo. `latitude`/`longitude` aceitos no request
    mas não persistidos — sem coluna física correspondente ainda (`017-trip-occurrences.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        tipo: OccurrenceType,
        descricao: str,
        gravidade: OccurrenceSeverity | None,
        status: OccurrenceStatus,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.tipo = tipo
        self.descricao = descricao
        self.gravidade = gravidade
        self.status = status
        self.data_hora = data_hora

    @classmethod
    def create(
        cls,
        *,
        viagem_id: uuid.UUID,
        tipo: OccurrenceType,
        descricao: str,
        gravidade: OccurrenceSeverity | None,
        occurred_at: datetime,
    ) -> "Occurrence":
        return cls(
            id=uuid.uuid4(),
            viagem_id=viagem_id,
            tipo=tipo,
            descricao=descricao,
            gravidade=gravidade,
            status=OccurrenceStatus.ABERTA,
            data_hora=occurred_at,
        )

    def update(
        self,
        *,
        descricao: str | None,
        gravidade: OccurrenceSeverity | None,
        status: OccurrenceStatus | None,
    ) -> None:
        if descricao is not None:
            self.descricao = descricao
        if gravidade is not None:
            self.gravidade = gravidade
        if status is not None:
            self.status = status
