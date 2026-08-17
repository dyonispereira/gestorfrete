from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from modules.mobile.domain.value_objects.sync_item_status import SyncItemStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class SyncQueueItem(BaseAggregateRoot[uuid.UUID]):
    """`filas_sincronizacao` — D137: um comando atômico por item. D139: `payload` nunca é
    sobrescrito depois de criado; só `status`/`numero_tentativa`/`resolucao_conflito` mudam."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        sessao_mobile_id: uuid.UUID,
        sequencia_local: int,
        tipo_comando: str,
        entidade_destino_tipo: str,
        entidade_destino_id: uuid.UUID,
        payload: dict[str, Any],
        identificador_local_unico: str,
        numero_tentativa: int,
        status: SyncItemStatus,
        resolucao_conflito: str | None,
        criado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.sessao_mobile_id = sessao_mobile_id
        self.sequencia_local = sequencia_local
        self.tipo_comando = tipo_comando
        self.entidade_destino_tipo = entidade_destino_tipo
        self.entidade_destino_id = entidade_destino_id
        self.payload = payload
        self.identificador_local_unico = identificador_local_unico
        self.numero_tentativa = numero_tentativa
        self.status = status
        self.resolucao_conflito = resolucao_conflito
        self.criado_em = criado_em

    @classmethod
    def enqueue(
        cls,
        *,
        sessao_mobile_id: uuid.UUID,
        sequencia_local: int,
        tipo_comando: str,
        entidade_destino_tipo: str,
        entidade_destino_id: uuid.UUID,
        payload: dict[str, Any],
        identificador_local_unico: str,
        now: datetime,
    ) -> "SyncQueueItem":
        return cls(
            id=uuid.uuid4(), sessao_mobile_id=sessao_mobile_id, sequencia_local=sequencia_local,
            tipo_comando=tipo_comando, entidade_destino_tipo=entidade_destino_tipo,
            entidade_destino_id=entidade_destino_id, payload=payload,
            identificador_local_unico=identificador_local_unico, numero_tentativa=1,
            status=SyncItemStatus.PENDENTE, resolucao_conflito=None, criado_em=now,
        )

    def mark_processing(self) -> None:
        self.status = SyncItemStatus.ENVIANDO
        self.numero_tentativa += 1

    def mark_processed(self) -> None:
        self.status = SyncItemStatus.PROCESSADA

    def mark_failed(self) -> None:
        self.status = SyncItemStatus.FALHOU

    def mark_conflict(self, resolution: str) -> None:
        """D131 — resolvido sempre pelo backend; D139 — `payload` permanece intocado, a resolução é
        um campo adicional na mesma linha."""

        self.status = SyncItemStatus.CONFLITO
        self.resolucao_conflito = resolution
