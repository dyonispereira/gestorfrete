from __future__ import annotations

import uuid
from datetime import datetime

from modules.integration.domain.value_objects.job_result import JobResult
from shared_kernel.domain.base_entity import BaseEntity


class JobExecution(BaseEntity[uuid.UUID]):
    """`execucoes_job` (D037, Histórica — nunca editada após concluída). `POST /jobs/commands/
    trigger` só enfileira (`trigger()`, sem `data_hora_fim`/`resultado`); a execução em si fica fora
    do contrato (D322/D413) — `complete()` só é chamado por `JobInternalTransitions`, nunca por
    HTTP."""

    def __init__(
        self, id: uuid.UUID, *, tenant_id: uuid.UUID | None, tipo_job: str, data_hora_inicio: datetime,
        data_hora_fim: datetime | None, resultado: JobResult | None,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.tipo_job = tipo_job
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_fim = data_hora_fim
        self.resultado = resultado

    @classmethod
    def trigger(cls, *, tenant_id: uuid.UUID | None, tipo_job: str, now: datetime) -> "JobExecution":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, tipo_job=tipo_job, data_hora_inicio=now, data_hora_fim=None,
            resultado=None,
        )

    def complete(self, *, resultado: JobResult, now: datetime) -> None:
        self.data_hora_fim = now
        self.resultado = resultado
