from __future__ import annotations

import uuid

from modules.reporting.domain.value_objects.scheduled_update_mode import ScheduledUpdateMode
from shared_kernel.domain.base_entity import BaseEntity


class ScheduledUpdate(BaseEntity[uuid.UUID]):
    """`agendamentos_atualizacao` (D159) — nunca executa cálculo, só define a política. Exatamente
    um de `metrica_id`/`cubo_analitico_id` (`ck_agendamentos_atualizacao_alvo`)."""

    def __init__(
        self, id: uuid.UUID, *, tenant_id: uuid.UUID, metrica_id: uuid.UUID | None,
        cubo_analitico_id: uuid.UUID | None, modo: ScheduledUpdateMode, status: str,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.metrica_id = metrica_id
        self.cubo_analitico_id = cubo_analitico_id
        self.modo = modo
        self.status = status

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, metrica_id: uuid.UUID | None, cubo_analitico_id: uuid.UUID | None,
        modo: ScheduledUpdateMode,
    ) -> "ScheduledUpdate":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, metrica_id=metrica_id, cubo_analitico_id=cubo_analitico_id,
            modo=modo, status="ATIVO",
        )

    def update(self, *, modo: ScheduledUpdateMode | None, status: str | None) -> None:
        if modo is not None:
            self.modo = modo
        if status is not None:
            self.status = status
