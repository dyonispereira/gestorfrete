from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.analytics.domain.value_objects.snapshot_processing_origin import SnapshotProcessingOrigin
from modules.analytics.domain.value_objects.snapshot_status import SnapshotStatus
from shared_kernel.domain.base_entity import BaseEntity


class AnalyticalSnapshot(BaseEntity[uuid.UUID]):
    """`snapshots_analiticos` (D151) — imutável para sempre depois de `CONSOLIDADO`. D160 — "quais
    Métricas participaram" não é estado próprio desta entidade: é sempre derivado via junção com
    `snapshots_analiticos_indicadores`→`indicadores_consolidados` (nenhuma coluna redundante,
    `relational/011-bi.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        periodo_referencia: str,
        data_hora_consolidacao: datetime | None,
        origem_processamento: SnapshotProcessingOrigin,
        usuario_id: uuid.UUID | None,
        status: SnapshotStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.periodo_referencia = periodo_referencia
        self.data_hora_consolidacao = data_hora_consolidacao
        self.origem_processamento = origem_processamento
        self.usuario_id = usuario_id
        self.status = status

    @classmethod
    def start(
        cls, *, tenant_id: uuid.UUID, periodo_referencia: str, origem_processamento: SnapshotProcessingOrigin,
        usuario_id: uuid.UUID | None,
    ) -> "AnalyticalSnapshot":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, periodo_referencia=periodo_referencia,
            data_hora_consolidacao=None, origem_processamento=origem_processamento, usuario_id=usuario_id,
            status=SnapshotStatus.EM_PROCESSAMENTO,
        )

    def consolidate(self, *, now: datetime) -> None:
        """D151 — só permitido a partir de `EM_PROCESSAMENTO`; depois disso, esta é a última
        mutação possível na entidade para sempre."""

        if self.status != SnapshotStatus.EM_PROCESSAMENTO:
            raise ConflictError(
                "ANALYTICS_SNAPSHOT_NOT_IN_PROCESSING", "Snapshot não está em processamento."
            )
        self.data_hora_consolidacao = now
        self.status = SnapshotStatus.CONSOLIDADO

    def mark_invalid(self) -> None:
        if self.status != SnapshotStatus.EM_PROCESSAMENTO:
            raise ConflictError(
                "ANALYTICS_SNAPSHOT_ALREADY_CONSOLIDATED",
                "Snapshot já consolidado — D151 nunca reabre um snapshot fechado.",
            )
        self.status = SnapshotStatus.INVALIDO
